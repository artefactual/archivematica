"""
Task class, representing an individual command (usually run on a file or directory).
Stored in the `Task` model.

Tasks are passed to MCPClient for processing.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import os
import uuid

from main import models

from django.utils import timezone

from server.db import auto_close_old_connections


logger = logging.getLogger("archivematica.mcp.server.tasks")


class Task(object):
    """A task object, representing an individual command (usually run on a file or
    directory).

    Tasks are processed out of process by a `TaskBackend`, which passes them to
    MCPClient.
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
        self.stdout = ""
        self.stderr = ""

        self.start_timestamp = timezone.now()
        self.finished_timestamp = None

    def __repr__(self):
        return "Task(uuid={}, arguments={}, start_timestamp={}, done={})".format(
            self.uuid, self.arguments, self.start_timestamp, self.done
        )

    @classmethod
    @auto_close_old_connections()
    def cleanup_old_db_entries(cls):
        """Update the status of any in progress tasks.

        This command is run on startup.
        TODO: we could try to recover, instead of just failing.
        """
        models.Task.objects.filter(exitcode=None).update(
            exitcode=-1, stderror="MCP shut down while processing."
        )

    @classmethod
    @auto_close_old_connections()
    def bulk_log(self, tasks, job):
        """Log tasks to the database, in bulk."""
        model_objects = [task.to_db_model(job) for task in tasks]
        models.Task.objects.bulk_create(model_objects)

    def to_db_model(self, job):
        """Returns an instance of the `Task` Django model."""
        job_uuid = job.uuid
        file_uuid = self.context.get(r"%fileUUID%", "")
        task_exec = job.link.config.get("execute")
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
        Write the stdout/stderror we got from MCP Client out to files,
        if necessary.
        """
        if self.stdout_file_path and self.stdout:
            self._write_file_to_disk(self.stdout_file_path, self.stdout)
        if self.stderr_file_path and self.stderr:
            self._write_file_to_disk(self.stderr_file_path, self.stderr)
