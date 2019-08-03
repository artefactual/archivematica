"""
JobChain and JobChainLink bridge workflow steps and jobs that can be run.
"""
from __future__ import unicode_literals

import logging
import uuid

from django.conf import settings
from django.utils import six, timezone

import metrics
from db import auto_close_old_connections
from task import GearmanTaskRequest, Task, wait_for_gearman_task_results

from main import models


logger = logging.getLogger("archivematica.mcp.server")


class JobChain(object):
    """
    Creates jobs as necessary based on the workflow chain and package given.
    """

    def __init__(self, package, chain, workflow, starting_link=None):
        """Create an instance of a chain, based on the workflow chain given."""
        self.package = package
        self.chain = chain
        self.workflow = workflow
        self.started_on = timezone.now()
        self.current_link = None
        self.current_job = None
        self.next_link = starting_link or self.chain.link
        # TODO: package context hits the db, make that clearer
        self.context = self.package.context.copy()

        # TODO: store generated choices in context
        self.generated_choices = None

        logger.debug(
            "Creating JobChain %s for package %s (initial link %s)",
            chain.id,
            package.uuid,
            self.current_link,
        )

    def __iter__(self):
        return self

    def __next__(self):
        if self.next_link:
            next_link = self.next_link
            self.next_link = None
        else:
            try:
                next_link = self.current_link.get_next_link(self.current_job.exit_code)
            except KeyError:
                next_link = None

        if self.current_job is not None:
            self.job_completed()

        if next_link:
            self.current_link = next_link
            self.current_job = Job.job_for_link_type(
                self, self.current_link, self.package
            )
            return self.current_job
        else:
            self.current_link = None
            self.current_job = None
            self.chain_completed()
            raise StopIteration

    next = __next__  # py2 compatability

    @property
    def id(self):
        return self.chain.id

    def job_completed(self):
        logger.debug(
            "%s %s done with exit code %s",
            self.current_job.__class__.__name__,
            self.current_job.uuid,
            self.current_job.exit_code,
        )
        job_status = self.current_link.get_status_id(self.current_job.exit_code)
        self.current_job.update_job_status(job_status)

    def chain_completed(self):
        """Log chain completion
        """
        logger.debug(
            "Done with chain %s for package %s", self.chain.id, self.package.uuid
        )
        completed_on = timezone.now()
        chain_duration = (completed_on - self.started_on).total_seconds()
        metrics.chain_completed(chain_duration, self.package.__class__.__name__)


class Job(object):
    """
    A single job, corresponding to a workflow link. Links the Job model in the database.
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

        # always zero for non task jobs
        self.exit_code = 0

    @classmethod
    def job_for_link_type(cls, job_chain, link, package):
        manager_name = link.config["@manager"]
        if manager_name in (
            "linkTaskManagerDirectories",
            "linkTaskManagerFiles",
            "linkTaskManagerGetMicroserviceGeneratedListInStdOut",
        ):
            job_class = TaskJob
        else:
            job_class = cls

        return job_class(job_chain, link, package)

    @property
    def name(self):
        return self.link.config.get("execute", "").lower()

    @auto_close_old_connections
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

        # The manager will populate Job tasks, via add_task
        manager_class = self.link.manager
        manager = manager_class(self, self.package)
        manager.execute()

        return self

    @auto_close_old_connections
    def update_job_status(self, status_code):
        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=status_code
        )

    @auto_close_old_connections
    def mark_awaiting_decision(self):
        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=self.STATUS_AWAITING_DECISION
        )

    @auto_close_old_connections
    def mark_complete(self):
        return models.Job.objects.filter(jobuuid=self.uuid).update(
            currentstep=self.STATUS_COMPLETED_SUCCESSFULLY
        )


class TaskJob(Job):
    """A job with one or more tasks, executed via mcp client script.
    """

    # The number of files we'll pack into each MCP Client job.  Chosen somewhat
    # arbitrarily, but benchmarking with larger values (like 512) didn't make much
    # difference to throughput.
    #
    # Setting this too large will use more memory; setting it too small will hurt
    # throughput.  So the trick is to set it juuuust right.
    TASK_BATCH_SIZE = settings.BATCH_SIZE

    def __init__(self, *args, **kwargs):
        super(TaskJob, self).__init__(*args, **kwargs)

        # Exit code is the maximum task exit code
        self.exit_code = None

        self.tasks = {}
        self.pending_task_ids = []
        self.task_request = None
        self.task_requests = []
        self.callbacks = []

    @property
    def name(self):
        return self.link.config.get("execute", "").lower()

    @auto_close_old_connections
    def run(self, *args, **kwargs):
        super(TaskJob, self).run(*args, **kwargs)

        if self.tasks:
            # Submit the last batch
            self.submit_task_batch()

            # Block until out of process tasks have completed
            self.wait_for_task_results()

            # Log tasks to DB
            model_objects = [
                task.to_db_model(self, self.link) for task in six.itervalues(self.tasks)
            ]
            models.Task.objects.bulk_create(model_objects, batch_size=2000)
        else:
            # Force exit code 0 if we didn't run any tasks
            self.exit_code = 0

        for callback in self.callbacks:
            callback(self)

        return self

    def submit_task_batch(self):
        if self.task_request is None:
            return

        self.task_request.submit(self.name)
        self.task_requests.append(self.task_request)
        self.task_request = None

    def add_task(self, *args, **kwargs):
        task = Task(*args, **kwargs)
        self.tasks[str(task.uuid)] = task

        if self.task_request is None:
            self.task_request = GearmanTaskRequest()
        self.task_request.add_task(task)

        if (len(self.task_request) % self.TASK_BATCH_SIZE) == 0:
            self.submit_task_batch()

    def wait_for_task_results(self):
        for task_id, task_result in wait_for_gearman_task_results(self.task_requests):
            task = self.tasks[task_id]
            task.exit_code = task_result["exitCode"]
            task.exit_status = task_result.get("exitStatus", "")
            task.stdout = task_result.get("stdout", "")
            task.stderr = task_result.get("stderr", "")
            task.finished_timestamp = task_result.get("finishedTimestamp")

            # task.write_output()

            self.exit_code = max([self.exit_code, task.exit_code])
            metrics.task_completed(task, self)

    def add_callback(self, callback):
        """Adds a callback to be executed after job execution"""
        self.callbacks.append(callback)
