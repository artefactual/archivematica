# -*- coding: utf-8 -*-

"""
Jobs remotely executed by on MCP client.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import abc
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


@six.add_metaclass(abc.ABCMeta)
class ClientScriptJob(Job):
    """A job with one or more Tasks, executed via mcp client script.

    Tasks are batched into groups of TASK_BATCH_SIZE, sent to mcp client via gearman.
    For task details, see the `Task` and `GearmanTaskBackend` classes.
    """

    # The number of files we'll pack into each MCP Client job.  Chosen somewhat
    # arbitrarily, but benchmarking with larger values (like 512) didn't make much
    # difference to throughput.
    #
    # Setting this too large will use more memory; setting it too small will hurt
    # throughput.  So the trick is to set it juuuust right.
    TASK_BATCH_SIZE = settings.BATCH_SIZE

    # If True, request stdout/stderr be returned by mcp client in task results
    capture_task_output = False

    def __init__(self, *args, **kwargs):
        super(ClientScriptJob, self).__init__(*args, **kwargs)

        # Lazy initialize in `run` method
        self.task_backend = None

        # Exit code is the maximum task exit code; start with None
        self.exit_code = None

        self.command_replacements = {}

    @property
    def name(self):
        """The name of the job, e.g. "normalize_v1.0".

        Passed to MCPClient to determine the task to run.
        """
        return self.link.config.get("execute", "").lower()

    @property
    def arguments(self):
        """Raw arguments for the task, as defined by the workflow prior to
        value replacement.
        """
        return self.link.config.get("arguments")

    @property
    def stdout_file(self):
        """A file path to capture job stdout, as defined in the workflow."""
        return self.link.config.get("stdout_file")

    @property
    def stderr_file(self):
        """A file path to capture job stderr, as defined in the workflow."""
        return self.link.config.get("stderr_file")

    @staticmethod
    def replace_values(command, replacements):
        """Replace variables in a string with any replacements given in a dict.

        A large number of replacement values are available. For more details see
        `get_replacement_mapping` and `get_file_replacement_mapping` in the `packages`
        module.
        """
        if command is None:
            return None

        for key, replacement in six.iteritems(replacements):
            escaped_replacement = _escape_for_command_line(replacement)
            command = command.replace(key, escaped_replacement)

        return command

    @auto_close_old_connections()
    def run(self, *args, **kwargs):
        super(ClientScriptJob, self).run(*args, **kwargs)

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
            self.exit_code = max([self.exit_code or 0, task.exit_code or 0])
            metrics.task_completed(task, self)
            self.task_completed_callback(task)

    def task_completed_callback(self, task):
        """Hook for child classes."""

    @auto_close_old_connections()
    def update_status_from_exit_code(self):
        status_code = self.link.get_status_id(self.exit_code)

        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=status_code
        )


class DirectoryClientScriptJob(ClientScriptJob):
    """
    A job with one Task, passing a directory path.

    Fully implemented in ClientScriptJob.
    """


class FilesClientScriptJob(ClientScriptJob):
    """
    A job with many tasks, one per file.
    """

    @property
    def filter_file_start(self):
        """Returns path prefix to filter files on, as defined in the workflow."""
        return self.link.config.get("filter_file_start", "")

    @property
    def filter_file_end(self):
        """Returns path suffix to filter files on, as defined in the workflow."""
        return self.link.config.get("filter_file_end", "")

    @property
    @auto_close_old_connections()
    def filter_subdir(self):
        """Returns directory to filter files on.

        This path is usually defined in the workflow but can be overridden
        per package in a UnitVariable, so we need to look that up.
        """

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
        """Iterate through all matching files for the package, and submit tasks."""
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
    """Retrieves output (e.g. a set of choices) from mcp client, for use in a decision.

    Output is returned via stderr, and parsed via eval. It is stored for access by the
    next job on the `generated_choices` attribute of the job chain, which is used for
    only this purpose.

    TODO: Remove from workflow if possible.
    """

    # We always need output for this type of job
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
