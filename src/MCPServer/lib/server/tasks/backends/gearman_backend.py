"""
Gearman task backend. Submits `Task` objects to gearman for processing,
and returns results.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import uuid

from django.conf import settings
from django.utils.six.moves import cPickle
from gearman import GearmanClient
from gearman.constants import JOB_COMPLETE, JOB_FAILED, JOB_UNKNOWN
import six

from server import metrics
from server.tasks.task import Task
from server.tasks.backends.base import TaskBackend


logger = logging.getLogger("archivematica.mcp.server.jobs.tasks")


class MCPGearmanClient(GearmanClient):
    """
    Client that adds `wait_until_any_job_completed`, so that we can poll a bit
    more efficiently.
    """

    def wait_until_any_job_completed(self, job_requests, poll_timeout=None):
        """
        Go into a select loop until any of our jobs have completed or failed.

        This is a modified version of `wait_until_jobs_completed`.
        """

        def continue_while_no_job_completed(any_activity):
            """Returns False (exiting the poll loop) if anything was completed."""
            for current_request in job_requests:
                if current_request.complete and current_request.state != JOB_UNKNOWN:
                    return False

            return True

        self.poll_connections_until_stopped(
            self.connection_list, continue_while_no_job_completed, timeout=poll_timeout
        )

        # Mark any job still in the queued state to poll_timeout
        for current_request in job_requests:
            if current_request.complete:
                self.request_to_rotating_connection_queue.pop(current_request, None)

        return job_requests


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
        self.client = MCPGearmanClient([settings.GEARMAN_SERVER])

        self.current_task_batches = {}  # job_uuid: GearmanTaskBatch
        self.pending_gearman_jobs = {}  # job_uuid: List[GearmanTaskBatch]

    def submit_task(self, job, task):
        """Submit a `Task` (as part of the `Job` given) for processing.

        We add the task to the batch, and only actually send the batch
        to gearman if it's "full".
        """
        current_task_batch = self._get_current_task_batch(job.uuid)
        if len(current_task_batch) == 0:
            metrics.gearman_pending_jobs_gauge.inc()

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

        # Make sure everything has been accepted by gearman before getting results
        # Note that accepted here means STATE_PENDING, that is accepted by the
        # gearman server, not a client.
        self.client.wait_until_jobs_accepted(gearman_requests)

        while len(pending_batches) > completed_request_count:
            gearman_requests = self.client.wait_until_any_job_completed(
                gearman_requests
            )

            for batch in pending_batches:
                if batch.collected:
                    continue

                if batch.complete or batch.failed:
                    for task in batch.update_task_results():
                        yield task

                    batch.collected = True
                    completed_request_count += 1
                    metrics.gearman_active_jobs_gauge.dec()

            # Only keep checking unfinished requests
            gearman_requests = [
                request
                for request in gearman_requests
                if request.state not in (JOB_COMPLETE, JOB_FAILED)
            ]

        # Once we've gotten results for all job tasks, clear the batches
        del self.pending_gearman_jobs[job.uuid]

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
        if len(task_batch) == 0:
            return

        task_batch.submit(self.client, job)

        metrics.gearman_active_jobs_gauge.inc()
        metrics.gearman_pending_jobs_gauge.dec()

        if job.uuid not in self.pending_gearman_jobs:
            self.pending_gearman_jobs[job.uuid] = []
        self.pending_gearman_jobs[job.uuid].append(task_batch)

        # Clear the current task batch
        if self.current_task_batches[job.uuid] is task_batch:
            del self.current_task_batches[job.uuid]


class GearmanTaskBatch(object):
    """A collection of `Task` objects, to be submitted as one gearman job."""

    def __init__(self):
        self.uuid = uuid.uuid4()
        self.tasks = []
        self.pending = None
        self.collected = False

    def __len__(self):
        return len(self.tasks)

    @property
    def complete(self):
        return self.pending and self.pending.state == JOB_COMPLETE

    @property
    def failed(self):
        return self.pending and self.pending.state == JOB_FAILED

    def serialize_task(self, task):
        return {
            "uuid": six.text_type(task.uuid),
            "createdDate": task.start_timestamp.isoformat(str(" ")),
            "arguments": task.arguments,
            "wants_output": task.wants_output,
        }

    def add_task(self, task):
        self.tasks.append(task)

    def submit(self, client, job):
        # Log tasks to DB, before submitting the batch, as mcpclient then updates them
        Task.bulk_log(self.tasks, job)

        data = {"tasks": {}}
        for task in self.tasks:
            task_uuid = six.text_type(task.uuid)
            data["tasks"][task_uuid] = self.serialize_task(task)

        pickled_data = cPickle.dumps(data, protocol=0)

        self.pending = client.submit_job(
            task=six.ensure_binary(job.name),
            data=pickled_data,
            unique=six.ensure_binary(six.text_type(self.uuid)),
            wait_until_complete=False,
            background=False,
            max_retries=0,
        )
        logger.debug("Submitted gearman job %s (%s)", self.uuid, job.name)

    def result(self):
        if not self.complete:
            raise RuntimeError("Gearman task hasn't been executed yet")
        elif not self.pending.result:
            raise ValueError("Unexpected empty result from Gearman job")

        job_result = cPickle.loads(self.pending.result)

        try:
            return job_result["task_results"]
        except KeyError:
            raise ValueError(
                "Expected a map containing 'task_results', but got: {!r}".format(
                    job_result
                )
            )

    def update_task_results(self):
        if self.failed:
            logger.error("Gearman task batch %s failed to execute", self.uuid)

            for task in self.tasks:
                task.exit_code = 1
                task.done = True
                yield task
        else:
            result = self.result()
            for task in self.tasks:
                task_id = six.text_type(task.uuid)
                task_result = result[task_id]
                task.exit_code = task_result["exitCode"]
                task.stdout = task_result.get("stdout", "")
                task.stderr = task_result.get("stderr", "")
                task.finished_timestamp = task_result.get("finishedTimestamp")
                task.write_output()

                task.done = True

                logger.debug(
                    "Task %s finished! Result %s - %s",
                    task_id,
                    self.pending.state,
                    task_result["exitCode"],
                )

                yield task
