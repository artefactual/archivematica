"""
JobChain and JobChainLink bridge workflow steps and jobs that can be run.
"""
from __future__ import unicode_literals

import logging
import uuid

from django.utils import timezone

from databaseFunctions import auto_close_db

import metrics
from scheduler import package_scheduler
from utils import log_exceptions

from main import models


logger = logging.getLogger("archivematica.mcp.server")


class JobChain(object):
    """
    Creates jobs as necessary based on the workflow chain and package given.
    """

    def __init__(self, package, chain, workflow, starting_link=None):
        """Create an instance of a chain, based on the workflow chain given."""
        logger.debug("Creating JobChain %s for package %s", chain.id, package.uuid)
        self.package = package
        self.chain = chain
        self.workflow = workflow
        self.started_on = timezone.now()
        self.current_link = starting_link or self.chain.link
        self.context = None
        # TODO: store generated choices in context
        self.generated_choices = None

    @property
    def id(self):
        return self.chain.id

    def get_current_job(self):
        if not self.current_link:
            return None

        if self.context is None:
            # TODO: package context hits the db, make that clearer
            self.context = self.package.context.copy()

        return Job(self, self.current_link, self.package)

    @log_exceptions
    @auto_close_db
    def job_done(self, job, exit_code, next_link=None):
        """Job completion callback.

        It continues the workflow running the next chain link which is looked
        up in the workflow data unless determined by `next_link_id`. Before
        starting, the status of the job associated to this link is updated.
        """
        job_status = self.current_link.get_status_id(exit_code)
        job.update_job_status(job_status)

        if next_link is None:
            try:
                next_link = self.current_link.get_next_link(exit_code)
            except KeyError:
                pass

        self.current_link = next_link

        if next_link is None:
            self.done()
        else:
            # TODO: move this logic to queue?
            # Queue the next job
            next_job = self.get_current_job()
            package_scheduler.schedule_job(next_job)

    def done(self):
        """Log chain completion
        """
        logger.debug(
            "Done with chain %s for package %s", self.chain.id, self.package.uuid
        )
        completed_on = timezone.now()
        chain_duration = (completed_on - self.started_on).total_seconds()
        metrics.chain_completed(chain_duration, self.package.__class__.__name__)


class Job(object):
    """Links the Job model in dashboard to a link in the workflow.
    """

    # Mirror job model statuses
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

    def run(self):
        logger.info("Running %s (package %s)", self.description, self.package.uuid)
        # Reload the package, in case the path has changed
        self.package.reload()

        # Persist the job in the db
        models.Job.objects.create(
            jobuuid=self.uuid,
            jobtype=self.description,
            directory=self.package.current_path,
            sipuuid=self.package.uuid,
            currentstep=self.STATUS_EXECUTING_COMMANDS,
            unittype=self.package.JOB_UNIT_TYPE,
            microservicegroup=self.group,
            createdtime=self.created_at,
            createdtimedec=self.created_at.strftime("%f"),
            microservicechainlink=self.link.id,
        )

        manager_class = self.link.manager
        manager = manager_class(self, self.package)
        manager.execute()

        return self

    @log_exceptions
    @auto_close_db
    def update_job_status(self, status_code):
        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=status_code
        )

    @log_exceptions
    @auto_close_db
    def mark_awaiting_decision(self):
        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=self.STATUS_AWAITING_DECISION
        )

    @log_exceptions
    @auto_close_db
    def mark_complete(self):
        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=self.STATUS_COMPLETED_SUCCESSFULLY
        )
