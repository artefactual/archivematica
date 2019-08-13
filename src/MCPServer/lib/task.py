"""
Collection of tasks that we'll send off to the MCPClient (via Gearman).

Each Job has one or more Tasks.
"""
from __future__ import unicode_literals

import abc
import gearman
import cPickle
import logging
import os
import threading
import uuid

from main import models

from django.conf import settings
from django.utils import six, timezone


logger = logging.getLogger("archivematica.mcp.server.task")
thread_locals = threading.local()


def gearman_client():
    if not hasattr(thread_locals, "client"):
        thread_locals.client = gearman.GearmanClient([settings.GEARMAN_SERVER])

    return thread_locals.client


class Task(object):
    """A task object, representing an indiviual command (usually run on a file or
    directory).

    Tasks are batched together and sent to mcp client for processing.
    """

    def __init__(
        self, arguments, stdout_file_path, stderr_file_path, context, wants_output=False
    ):
        self.uuid = uuid.uuid4()
        self.done = False
        self.arguments = arguments
        self.stdout_file_path = stdout_file_path
        self.stderr_file_path = stderr_file_path
        self.context = context

        self.wants_output = any([wants_output, stdout_file_path, stderr_file_path])

        self.exit_code = None
        self.exit_status = ""
        self.stdout = ""
        self.stderr = ""

        self.start_timestamp = timezone.now()
        self.finished_timestamp = None

    def to_db_model(self, job, link):
        job_uuid = job.uuid
        file_uuid = self.context.get(r"%fileUUID%", "")
        task_exec = link.config.get("execute")
        file_name = os.path.basename(
            os.path.abspath(self.context[r"%relativeLocation%"])
        )

        return models.Task(
            taskuuid=self.uuid,
            job_id=job_uuid,
            fileuuid=file_uuid,
            filename=file_name,
            execution=task_exec,
            arguments=self.arguments,
            createdtime=self.start_timestamp,
        )

    def _write_file_to_disk(self, path, contents):
        """Write the bytes in ``contents`` to ``path`` in append mode.

        The mode of ``path`` is adjusted to ensure that it's not readable by
        ``others``.
        """
        try:
            with open(path, "a") as f:
                f.write(contents)
            os.chmod(path, 0o750)
        except Exception:
            logger.exception("Unable to write to: %s", path)

    def write_output(self):
        """
        Write the stdout/stderror we got from MCP Client out to files if
        necessary.
        """
        if self.stdout_file_path and self.stdout:
            self._write_file_to_disk(self.stdout_file_path, self.stdout)
        if self.stderr_file_path and self.stderr:
            self._write_file_to_disk(self.stderr_file_path, self.stderr)


@six.add_metaclass(abc.ABCMeta)
class TaskRequest(object):
    @abc.abstractmethod
    def add_task(self, task):
        """Add a task prior to submission"""
        raise NotImplementedError

    @abc.abstractmethod
    def submit(self):
        """Submit tasks for offline processing (e.g. via gearman)"""
        raise NotImplementedError

    @abc.abstractmethod
    def result(self):
        """Return the job result after processing"""
        raise NotImplementedError


class GearmanTaskRequest(TaskRequest):
    def __init__(self):
        self.uuid = uuid.uuid4()
        self.tasks = []
        self.pending = None

    def __len__(self):
        return len(self.tasks)

    def serialize_task(self, task):
        return {
            "uuid": str(task.uuid),
            "createdDate": task.start_timestamp.isoformat(b" "),
            "arguments": task.arguments,
            "wants_output": task.wants_output,
        }

    def add_task(self, task):
        self.tasks.append(task)

    def submit(self, task_name):
        client = gearman_client()

        data = {"tasks": {}}
        for task in self.tasks:
            data["tasks"][str(task.uuid)] = self.serialize_task(task)

        pickled_data = cPickle.dumps(data)

        self.pending = client.submit_job(
            task=six.binary_type(task_name),
            data=pickled_data,
            unique=six.binary_type(self.uuid),
            wait_until_complete=False,
            background=False,
            max_retries=0,
        )
        logger.debug("Submitted gearman job %s (%s)", self.uuid, task_name)

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


def wait_for_gearman_task_results(task_requests):
    """Generator that yields task results as they arrive from gearman.
    """
    client = gearman_client()

    completed_request_count = 0
    gearman_requests = [request.pending for request in task_requests]

    while len(task_requests) > completed_request_count:
        try:
            gearman_requests = client.get_job_statuses(gearman_requests)
        except KeyError:
            # Annoying gearman bug: https://github.com/Yelp/python-gearman/issues/13
            # TODO: upgrade gearman
            gearman_requests = client.get_job_statuses(gearman_requests)

        for request in task_requests:
            if request.pending.complete:
                for task_id, task_result in six.iteritems(request.result()):
                    logger.debug(
                        "Task %s finished! Result %s - %s",
                        task_id,
                        request.pending.state,
                        task_result["exitCode"],
                    )
                    yield task_id, task_result

                completed_request_count += 1
