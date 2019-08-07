"""
JobChain and JobChainLink bridge workflow steps and jobs that can be run.
"""
from __future__ import unicode_literals

import logging
import uuid

from django.utils import timezone

from databaseFunctions import auto_close_db

import metrics
from utils import log_exceptions

from main import models


logger = logging.getLogger("archivematica.mcp.server")


class JobChain(object):
    """
    Creates jobs as necessary based on the workflow chain and unit given.
    """

    def __init__(self, unit, chain, workflow, starting_link=None):
        """Create an instance of a chain, based on the workflow chain given."""
        logger.debug("Creating JobChain %s for chain %s", unit, chain.id)
        self.unit = unit
        self.chain = chain
        self.workflow = workflow
        self.started_on = timezone.now()
        self.starting_link = starting_link or self.chain.link
        self.context = None
        # TODO: store generated choices in context
        self.generated_choices = None

    def start(self):
        # TODO: unit context hits the db, make that clearer
        self.context = self.unit.context.copy()

        job = Job(self, self.starting_link, self.workflow, self.unit)
        job.start()

    def proceed_to_next_link(self, link, context=None):
        """Proceed to next link."""
        if link is None:
            logger.debug(
                "Done with chain %s for unit %s", self.chain.id, self.unit.uuid
            )
            completed_on = timezone.now()
            chain_duration = (completed_on - self.started_on).total_seconds()
            metrics.chain_completed(chain_duration, self.unit.__class__.__name__)
            return

        job = Job(self, link, self.workflow, self.unit)
        job.start()


class Job(object):
    """Links the Job model in dashboard to a link in the workflow.
    """

    # Mirror job model statuses
    STATUS_UNKNOWN = models.Job.STATUS_UNKNOWN
    STATUS_AWAITING_DECISION = models.Job.STATUS_AWAITING_DECISION
    STATUS_COMPLETED_SUCCESSFULLY = models.Job.STATUS_COMPLETED_SUCCESSFULLY
    STATUS_EXECUTING_COMMANDS = models.Job.STATUS_EXECUTING_COMMANDS
    STATUS_FAILED = models.Job.STATUS_FAILED

    def __init__(self, job_chain, link, workflow, unit):
        self.uuid = uuid.uuid4()
        self.job_chain = job_chain
        self.workflow = workflow
        self.unit = unit
        self.link = link
        self.workflow = workflow
        self.created_at = timezone.now()
        self.group = link.get_label("group", "en")
        self.description = link.get_label("description", "en")

    def start(self):
        logger.info("Running %s (unit %s)", self.description, self.unit.uuid)
        # Reload the package, in case the path has changed
        self.unit.reload()

        # Persist the job in the db
        models.Job.objects.create(
            jobuuid=self.uuid,
            jobtype=self.description,
            directory=self.unit.current_path,
            sipuuid=self.unit.uuid,
            currentstep=self.STATUS_EXECUTING_COMMANDS,
            unittype=self.unit.JOB_UNIT_TYPE,
            microservicegroup=self.group,
            createdtime=self.created_at,
            createdtimedec=self.created_at.strftime("%f"),
            microservicechainlink=self.link.id,
        )

        manager_class = self.link.manager
        manager = manager_class(self, self.unit)
        manager.execute()

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

    @log_exceptions
    @auto_close_db
    def on_complete(self, exit_code, next_link=None):
        """Link completion callback.

        It continues the workflow running the next chain link which is looked
        up in the workflow data unless determined by `next_link_id`. Before
        starting, the status of the job associated to this link is updated.
        """
        job_status = self.link.get_status_id(exit_code)
        self.update_job_status(job_status)
        if next_link is None:
            try:
                next_link = self.link.get_next_link(exit_code)
            except KeyError:
                pass

        self.job_chain.proceed_to_next_link(next_link)
