"""
Gearman task backend. Submits `Task` objects to gearman for processing,
and returns results.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import uuid

import gearman
from django.conf import settings
from django.utils import six
from django.utils.six.moves import cPickle

from server.tasks.task import Task
from server.tasks.backends.base import TaskBackend


logger = logging.getLogger("archivematica.mcp.server.jobs.tasks")


class GearmanTaskBackend(TaskBackend):
    """Submits tasks to MCPClient via Gearman.

    Tasks are batched into BATCH_SIZE groups (default 128), pickled and sent to
    MCPClient. This adds some complexity but saves a lot of overhead.
    """

    # The number of files we'll pack into each MCP Client job.  Chosen somewhat
    # arbitrarily, but benchmarking with larger values (like 512) didn't make much
    # difference to throughput.
    #
    # Setting this too large will use more memory; setting it too small will hurt
    # throughput.  So the trick is to set it juuuust right.
    TASK_BATCH_SIZE = settings.BATCH_SIZE

    def __init__(self):
        self.client = gearman.GearmanClient([settings.GEARMAN_SERVER])

        self.current_task_batches = {}  # job_uuid: GearmanTaskBatch
        self.pending_gearman_jobs = {}  # job_uuid: List[GearmanTaskBatch]

    def submit_task(self, job, task):
        """Submit a `Task` (as part of the `Job` given) for processing.

        We add the task to the batch, and only actually send the batch
        to gearman if it's "full".
        """
        current_task_batch = self._get_current_task_batch(job.uuid)
        current_task_batch.add_task(task)

        # If we've hit TASK_BATCH_SIZE, send the batch to gearman
        if (len(current_task_batch) % self.TASK_BATCH_SIZE) == 0:
            self._submit_batch(job, current_task_batch)

    def wait_for_results(self, job):
        # Check if we have anything for this job that hasn't been submitted
        current_task_batch = self._get_current_task_batch(job.uuid)
        if len(current_task_batch) > 0:
            self._submit_batch(job, current_task_batch)

        try:
            pending_batches = self.pending_gearman_jobs[job.uuid]
        except KeyError:
            # No batches submitted
            return

        completed_request_count = 0
        gearman_requests = [request.pending for request in pending_batches]

        while len(pending_batches) > completed_request_count:
            try:
                gearman_requests = self.client.get_job_statuses(gearman_requests)
            except KeyError:
                # Annoying gearman bug: https://github.com/Yelp/python-gearman/issues/13
                # TODO: upgrade gearman
                gearman_requests = self.client.get_job_statuses(gearman_requests)

            for batch in pending_batches:
                if batch.pending.complete:
                    result = batch.result()
                    for task in batch.tasks:
                        task_id = six.text_type(task.uuid)
                        task_result = result[task_id]

                        task.exit_code = task_result["exitCode"]
                        task.exit_status = task_result.get("exitStatus", "")
                        task.stdout = task_result.get("stdout", "")
                        task.stderr = task_result.get("stderr", "")
                        task.finished_timestamp = task_result.get("finishedTimestamp")

                        task.write_output()

                        logger.debug(
                            "Task %s finished! Result %s - %s",
                            task_id,
                            batch.pending.state,
                            task_result["exitCode"],
                        )

                        yield task

                    completed_request_count += 1

        # Once we've gotten results for all tasks, delete the batches
        del self.pending_gearman_jobs[job.uuid]
        del self.current_task_batches[job.uuid]

    def _get_current_task_batch(self, job_uuid):
        """Return the current GearmanTaskBatch for the job, or initialize a new
        one.
        """
        try:
            return self.current_task_batches[job_uuid]
        except KeyError:
            self.current_task_batches[job_uuid] = GearmanTaskBatch()
            return self.current_task_batches[job_uuid]

    def _submit_batch(self, job, task_batch):
        task_batch.submit(self.client, job)
        if job.uuid not in self.pending_gearman_jobs:
            self.pending_gearman_jobs[job.uuid] = []
        self.pending_gearman_jobs[job.uuid].append(task_batch)


class GearmanTaskBatch(object):
    """A collection of `Task` objects, to be submitted as one gearman job.
    """

    def __init__(self):
        self.uuid = uuid.uuid4()
        self.tasks = []
        self.pending = None

    def __len__(self):
        return len(self.tasks)

    def serialize_task(self, task):
        return {
            "uuid": six.text_type(task.uuid),
            "createdDate": task.start_timestamp.isoformat(b" "),
            "arguments": task.arguments,
            "wants_output": task.wants_output,
        }

    def add_task(self, task):
        self.tasks.append(task)

    def submit(self, client, job):
        if len(self.tasks) == 0:
            return

        # Log tasks to DB, before submitting the batch, as mcpclient then updates them
        Task.bulk_log(self.tasks, job)

        data = {"tasks": {}}
        for task in self.tasks:
            task_uuid = six.text_type(task.uuid)
            data["tasks"][task_uuid] = self.serialize_task(task)

        pickled_data = cPickle.dumps(data)

        self.pending = client.submit_job(
            task=six.binary_type(job.name),
            data=pickled_data,
            unique=six.binary_type(self.uuid),
            wait_until_complete=False,
            background=False,
            max_retries=0,
        )
        logger.debug("Submitted gearman job %s (%s)", self.uuid, job.name)

    def result(self):
        if not (self.pending and self.pending.complete):
            raise RuntimeError("Gearman task hasn't been executed yet")
        elif not self.pending.result:
            raise RuntimeError("Unexpected empty result from Gearman job")

        job_result = cPickle.loads(self.pending.result)

        try:
            return job_result["task_results"]
        except KeyError:
            raise RuntimeError(
                "Expected a map containing 'task_results', but got: {!r}".format(
                    job_result
                )
            )
