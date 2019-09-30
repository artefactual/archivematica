# -*- coding: utf-8 -*-

"""
Base class for Job.
"""
from __future__ import unicode_literals

import logging
import uuid

from django.utils import timezone

from server.db import auto_close_old_connections

from main import models


logger = logging.getLogger("archivematica.mcp.server.jobs")


class Job(object):
    """
    A single job, corresponding to a workflow link, and the `Job` model in the database.

    There are various types of jobs, handled by subclasses:
        * `ClientScriptJob`, handling Jobs to be execute on MCPClient
        * `DecisionJob`, handling workflow decision points
        * `LocalJob`, handling work done directly on MCPServer
    """

    # Mirror job model statuses
    STATUSES = models.Job.STATUS
    STATUS_UNKNOWN = models.Job.STATUS_UNKNOWN
    STATUS_AWAITING_DECISION = models.Job.STATUS_AWAITING_DECISION
    STATUS_COMPLETED_SUCCESSFULLY = models.Job.STATUS_COMPLETED_SUCCESSFULLY
    STATUS_EXECUTING_COMMANDS = models.Job.STATUS_EXECUTING_COMMANDS
    STATUS_FAILED = models.Job.STATUS_FAILED

    def __init__(self, job_chain, link, package):
        self.uuid = uuid.uuid4()
        self.job_chain = job_chain
        self.package = package
        self.link = link
        self.created_at = timezone.now()
        self.group = link.get_label("group", "en")
        self.description = link.get_label("description", "en")

        # always zero for non task jobs
        self.exit_code = 0

    @property
    def name(self):
        return self.link.config.get("execute", "").lower()

    @classmethod
    @auto_close_old_connections
    def cleanup_old_db_entries(cls):
        models.Job.objects.filter(currentstep=cls.STATUS_AWAITING_DECISION).delete()
        models.Job.objects.filter(currentstep=cls.STATUS_EXECUTING_COMMANDS).update(
            currentstep=cls.STATUS_FAILED
        )

    @auto_close_old_connections
    def run(self):
        """
        Run the actual job.

        This method is executed via ThreadPoolExecutor and returns the _next_ job
        to process.
        """
        raise NotImplementedError

    @auto_close_old_connections
    def save_to_db(self):
        return models.Job.objects.create(
            jobuuid=self.uuid,
            jobtype=self.description,
            directory=self.package.current_path_for_db,
            sipuuid=self.package.uuid,
            currentstep=self.STATUS_EXECUTING_COMMANDS,
            unittype=self.package.JOB_UNIT_TYPE,
            microservicegroup=self.group,
            createdtime=self.created_at,
            createdtimedec=float(self.created_at.strftime("0.%f")),
            microservicechainlink=self.link.id,
        )

    @auto_close_old_connections
    def mark_awaiting_decision(self):
        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=self.STATUS_AWAITING_DECISION
        )

    @auto_close_old_connections
    def mark_complete(self):
        logger.debug(
            "%s %s done with exit code %s",
            self.__class__.__name__,
            self.uuid,
            self.exit_code,
        )
        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=self.STATUS_COMPLETED_SUCCESSFULLY
        )
