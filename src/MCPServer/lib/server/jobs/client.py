# -*- coding: utf-8 -*-

"""
Jobs remotely executed by on MCP client.
"""
from __future__ import unicode_literals

import ast
import logging

from django.conf import settings
from django.utils import six

from server import metrics
from server.db import auto_close_old_connections
from server.jobs.base import Job
from server.tasks import Task, get_task_backend

from main import models


logger = logging.getLogger("archivematica.mcp.server.jobs.client")


def _escape_for_command_line(value):
    # escape slashes, quotes, backticks
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    value = value.replace("`", "\`")

    return value


class ClientScriptJob(Job):
    """A job with one or more Tasks, executed via mcp client script.

    Tasks are batched into groups of TASK_BATCH_SIZE, sent to mcp client via gearman.
    """

    # The number of files we'll pack into each MCP Client job.  Chosen somewhat
    # arbitrarily, but benchmarking with larger values (like 512) didn't make much
    # difference to throughput.
    #
    # Setting this too large will use more memory; setting it too small will hurt
    # throughput.  So the trick is to set it juuuust right.
    TASK_BATCH_SIZE = settings.BATCH_SIZE

    capture_task_output = False

    def __init__(self, *args, **kwargs):
        super(ClientScriptJob, self).__init__(*args, **kwargs)

        # Lazy initialize in `run` method
        self.task_backend = None

        # Exit code is the maximum task exit code
        self.exit_code = None

        self.command_replacements = {}

    @property
    def arguments(self):
        return self.link.config.get("arguments")

    @property
    def stdout_file(self):
        return self.link.config.get("stdout_file")

    @property
    def stderr_file(self):
        return self.link.config.get("stderr_file")

    def replace_values(self, command, replacements):
        if command is None:
            return None

        for key, replacement in six.iteritems(replacements):
            escaped_replacement = _escape_for_command_line(replacement)
            command = command.replace(key, escaped_replacement)

        return command

    def run(self, *args, **kwargs):
        logger.info("Running %s (package %s)", self.description, self.package.uuid)

        # Reload the package, in case the path has changed
        self.package.reload()
        self.save_to_db()

        self.command_replacements = self.package.get_replacement_mapping(
            filter_subdir_path=self.link.config.get("filter_subdir")
        )
        if self.job_chain.context is not None:
            self.command_replacements.update(self.job_chain.context)

        self.task_backend = get_task_backend()
        self.submit_tasks()
        # Block until out of process tasks have completed
        self.wait_for_task_results()

        self.update_status_from_exit_code()

        return next(self.job_chain, None)

    def submit_tasks(self):
        arguments = self.replace_values(self.arguments, self.command_replacements)
        stdout_file = self.replace_values(self.stdout_file, self.command_replacements)
        stderr_file = self.replace_values(self.stderr_file, self.command_replacements)

        task = Task(
            arguments,
            stdout_file,
            stderr_file,
            self.command_replacements,
            wants_output=self.capture_task_output,
        )
        self.task_backend.submit_task(self, task)

    def wait_for_task_results(self):
        for task in self.task_backend.wait_for_results(self):
            self.exit_code = max([self.exit_code, task.exit_code])
            metrics.task_completed(task, self)
            self.task_completed_callback(task)

    def task_completed_callback(self, task):
        """Hook for child classes.
        """

    @auto_close_old_connections
    def update_status_from_exit_code(self):
        status_code = self.link.get_status_id(self.exit_code)

        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=status_code
        )


class DirectoryClientScriptJob(ClientScriptJob):
    """
    A job with one Task, passing a directory path.

    Note: same as the base ClientScriptJob
    """


class FilesClientScriptJob(ClientScriptJob):
    """
    A job with many tasks, one per file.
    """

    @property
    def filter_file_start(self):
        return self.link.config.get("filter_file_start", "")

    @property
    def filter_file_end(self):
        return self.link.config.get("filter_file_end", "")

    @property
    @auto_close_old_connections
    def filter_subdir(self):
        filter_subdir = self.link.config.get("filter_subdir", "")

        # Check if filterSubDir has been overridden for this Transfer/SIP
        try:
            var = models.UnitVariable.objects.get(
                unittype=self.package.UNIT_VARIABLE_TYPE,
                unituuid=self.package.uuid,
                variable=self.name,
            )
        except (
            models.UnitVariable.DoesNotExist,
            models.UnitVariable.MultipleObjectsReturned,
        ):
            var = None

        if var:
            try:
                script_override = ast.literal_eval(var.variablevalue)
            except (SyntaxError, ValueError):
                pass
            else:
                filter_subdir = script_override.get("filterSubDir")

        return filter_subdir

    def submit_tasks(self):
        for file_replacements in self.package.files(
            filter_filename_start=self.filter_file_start,
            filter_filename_end=self.filter_file_end,
            filter_subdir=self.filter_subdir,
        ):
            # File replacement values take priority
            command_replacements = self.command_replacements.copy()
            command_replacements.update(file_replacements)

            arguments = self.replace_values(self.arguments, command_replacements)
            stdout_file = self.replace_values(self.stdout_file, command_replacements)
            stderr_file = self.replace_values(self.stderr_file, command_replacements)

            task = Task(
                arguments,
                stdout_file,
                stderr_file,
                command_replacements,
                wants_output=self.capture_task_output,
            )
            self.task_backend.submit_task(self, task)
        else:
            # Nothing to do; set exit code to success
            self.exit_code = 0


class OutputClientScriptJob(ClientScriptJob):
    """Retrives output (e.g. a set of choices) from mcp client, for use in a decision."""

    capture_task_output = True

    def task_completed_callback(self, task):
        logger.debug("stdout emitted by client: %s", task.stdout)

        try:
            choices = ast.literal_eval(task.stdout)
        except (ValueError, SyntaxError):
            logger.exception("Unable to parse output %s", task.stdout)
            choices = {}

        # Store on chain for next job
        self.job_chain.generated_choices = choices
