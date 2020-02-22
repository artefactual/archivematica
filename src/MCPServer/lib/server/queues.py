# -*- coding: utf-8 -*-
"""
The PackageQueue class handles job queueing, as it relates to packages.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import functools
import logging
import Queue
import threading

from django.conf import settings
from django.utils import six

from server import metrics
from server.jobs import DecisionJob
from server.packages import DIP, SIP


logger = logging.getLogger("archivematica.mcp.server.queues")


class PackageQueue(object):
    """Package queue.

    This queue throttles `Job` objects belonging to packages, so that at most
    `CONCURRENT_PACKAGES` are active at any one time.

    It also tracks any jobs waiting for decisions in memory. This is a bit of
    a separate concern from package queuing and could be isolated in future.

    Methods on this class should be threadsafe; they can be called from any
    worker thread.

    This process happens when a `Job` is scheduled via `PackageQueue.schedule_job`.

    1. If there are too many active packages, the `Job` is placed on a deferred
       package queue and held until a package stops processing (packages stop
       processing when they reach a decision point in the workflow that hasn't
       been pre configured, or when they hit specific workflow links denoting
       SIP/Transfer completion or failure). If there is room to process the
       package, the job is placed on an active job queue, which is the consumed
       by the processing loop running on the main thread.
    2. The processing loop retrieves any jobs from the active queue, and
       schedules their `run` method for execution in a worker thread (via
       `ThreadPoolExecutor.submit`).
    3. The `Job.run` method executes. If it is a `ClientScriptJob` (executing
       on MCPClient), it generates the `Task` objects required, and sends them
       to MCPClient via `GearmanTaskBackend`, and waits for the results. All of
       this happens on the one worker thread.
    4. On the completion of tasks (i.e. results are returned by Gearman),
       `Job.run` returns the _next_ job to schedule, if any. In practice this
       is usually retrieved from the `JobChain` via `next(self.job_chain)`.
    5. Back in the main thread, a callback attached to the result of `Job.run`
       triggers adding the next job to the active job queue. This cycle
       continues until the workflow chain ends.
    """

    # TODO: make this better by signifying the end of a package in the workflow
    PACKAGE_COMPLETED_LINK_IDS = set(
        [
            # Move to SIP creation directory for completed transfers
            "d27fd07e-d3ed-4767-96a5-44a2251c6d0a",
            # Move to SIP Creation
            "39a128e3-c35d-40b7-9363-87f75091e1ff",
            # AIP completed
            "d5a2ef60-a757-483c-a71a-ccbffe6b80da",
            # Move SIP to failed directory
            "828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c",
            # Move Transfer to failed directory
            "377f8ebb-7989-4a68-9361-658079ff8138",
            # Move transfer to backlog
            "abd6d60c-d50f-4660-a189-ac1b34fafe85",
            # Move to the rejected directory
            "0d7f5dc2-b9af-43bf-b698-10fdcc5b014d",
            "333532b9-b7c2-4478-9415-28a3056d58df",
            "3467d003-1603-49e3-b085-e58aa693afed",
            # Failed compliance. See output in dashboard. SIP moved back to SIPsUnderConstruction
            "f025f58c-d48c-4ba1-8904-a56d2a67b42f",
            # Failed compliance. See output in dashboard. Transfer moved back to activeTransfers
            "61af079f-46a2-48ff-9b8a-0c78ba3a456d",
        ]
    )
    # An arbitrary, large value, so we don't accept infinite packages.
    MAX_QUEUED_PACKAGES = 4096

    def __init__(
        self,
        executor,
        shutdown_event=None,
        max_concurrent_packages=settings.CONCURRENT_PACKAGES,
        max_queued_packages=MAX_QUEUED_PACKAGES,
        debug=False,
    ):
        self.executor = executor
        self.max_concurrent_packages = max_concurrent_packages
        self.debug = debug

        if shutdown_event is None:
            shutdown_event = threading.Event()
        self.shutdown_event = shutdown_event

        self.waiting_choices_lock = threading.Lock()
        self.waiting_choices = {}  # job.uuid: DecisionJob

        self.active_package_lock = threading.Lock()
        self.active_packages = {}  # package uuid: Package

        self.job_queue = Queue.Queue(maxsize=max_concurrent_packages)

        # Split queues by package type
        self.transfer_queue = Queue.Queue(maxsize=max_queued_packages)
        self.sip_queue = Queue.Queue(maxsize=max_queued_packages)
        self.dip_queue = Queue.Queue(maxsize=max_queued_packages)

        if self.debug:
            logger.debug(
                "PackageQueue initialized. Max concurrent packages is %s.",
                self.max_concurrent_packages,
            )

    def schedule_job(self, job):
        """Add a job to the queue.

        If the Job's package is currently "active", it will be added to the
        active job queue for immediate processing. Otherwise, it will be
        queued, until a package has completed.
        """
        if self.shutdown_event.is_set():
            raise RuntimeError("Queue stopped.")

        # The most common case is an already active package is scheduled
        package = job.package
        with self.active_package_lock:
            if package.uuid in self.active_packages:
                # If there's no slot available, block until ready
                self.job_queue.put(job, block=True)
                metrics.job_queue_length_gauge.inc()
                return

            # Otherwise, we need to queue the package
            active_package_count = len(self.active_packages)

        self._put_package_nowait(package, job)

        if self.debug:
            with self.active_package_lock:
                logger.debug(
                    "Active packages are: %s",
                    ", ".join(
                        [
                            repr(active_package)
                            for active_package in self.active_packages.values()
                        ]
                    ),
                )
            queue_size = (
                self.sip_queue.qsize()
                + self.dip_queue.qsize()
                + self.transfer_queue.qsize()
            )
            logger.debug(
                "Scheduled job %s (%s %s). Current queue size: %s",
                job.uuid,
                package.__class__.__name__,
                package.uuid,
                queue_size,
            )

        # Don't start processing unless we have capacity
        if active_package_count < self.max_concurrent_packages:
            self.queue_next_job()

        elif self.debug:
            logger.debug(
                "Not processing next job; %s packages already active",
                active_package_count,
            )

    def work(self):
        """Process the package queue.

        Enters into an endless loop, pulling jobs from the queue and processing them,
        until `stop` is called.
        """
        while not self.shutdown_event.is_set():
            # Using a timeout here allows shutdown signals to fire
            self.process_one_job(timeout=1.0)

    def process_one_job(self, timeout=None):
        """Process a single job, if one is queued before `timeout`.

        Only called by `work` and unit tests.
        """
        # block until a job is waiting
        try:
            job = self.job_queue.get(timeout=timeout)
        except Queue.Empty:
            return

        metrics.job_queue_length_gauge.dec()
        metrics.active_jobs_gauge.inc()

        result = self.executor.submit(job.run)
        result.add_done_callback(self._job_completed_callback)

        if job.link.id in self.PACKAGE_COMPLETED_LINK_IDS:
            package_done_callback = functools.partial(
                self._package_completed_callback, job.package
            )
            result.add_done_callback(package_done_callback)

        return result

    def stop(self):
        """Trigger queue shutdown.
        """
        self.shutdown_event.set()

    def _package_completed_callback(self, package, future):
        """Called by an Executor on completion the last job in a package.

        The result of the future will always be None.
        """
        if future.result() is not None:
            raise RuntimeError(
                "Unexpectedly received another job on package completion. "
                "If the workflow has been modified, please update "
                "PACKAGE_COMPLETED_LINK_IDS."
            )

        self.deactivate_package(package)
        self.queue_next_job()

    def _job_completed_callback(self, future):
        """Called by an Executor on completion of `job.run`.

        The argument is a future, the result of which should be the next job
        in the chain.
        """
        metrics.active_jobs_gauge.dec()
        next_job = future.result()

        if not next_job:
            return

        # Special case for decision job here.
        if isinstance(next_job, DecisionJob) and next_job.awaiting_decision:
            self.await_decision(next_job)
        else:
            self.schedule_job(next_job)

    def _put_package_nowait(self, package, job):
        """Queue a package and job for later processing, after one of the
        currently active packages completes.
        """
        if isinstance(package, DIP):
            self.dip_queue.put_nowait(job)
        elif isinstance(package, SIP):
            self.sip_queue.put_nowait(job)
        else:
            self.transfer_queue.put_nowait(job)
        metrics.package_queue_length_gauge.labels(
            package_type=package.__class__.__name__
        ).inc()

    def _get_package_job_nowait(self):
        """Return a waiting job for an inactive package.
        Prioritized by package type.
        """
        try:
            job = self.dip_queue.get_nowait()
        except Queue.Empty:
            job = None

        if job is None:
            try:
                job = self.sip_queue.get_nowait()
            except Queue.Empty:
                pass

        if job is None:
            try:
                job = self.transfer_queue.get_nowait()
            except Queue.Empty:
                pass

        if job is not None:
            metrics.package_queue_length_gauge.labels(
                package_type=job.package.__class__.__name__
            ).dec()

        return job

    def activate_package(self, package):
        """Mark a package as active, allowing jobs related to it to process.
        """
        with self.active_package_lock:
            if package.uuid not in self.active_packages:
                self.active_packages[package.uuid] = package
                metrics.active_package_gauge.inc()
                if self.debug:
                    logger.debug("Marked package %s as active", package.uuid)
            else:
                logger.warning(
                    "Package %s was activated, but was already active", package.uuid
                )

    def deactivate_package(self, package):
        """Mark a package as inactive.
        """
        with self.active_package_lock:
            if package.uuid in self.active_packages:
                del self.active_packages[package.uuid]
                metrics.active_package_gauge.dec()
                if self.debug:
                    logger.debug("Marked package %s as inactive", package.uuid)
            else:
                logger.warning(
                    "Package %s was deactivated, but was not marked active",
                    package.uuid,
                )

    def queue_next_job(self):
        """Load another job into the active job queue.

        This method should only be called when there is space in the package
        queue.
        """
        job = self._get_package_job_nowait()
        if job is None:
            return  # nothing to do

        package = job.package
        self.activate_package(package)
        self.job_queue.put_nowait(job)
        metrics.job_queue_length_gauge.inc()

        if self.debug:
            queue_size = (
                self.sip_queue.qsize()
                + self.dip_queue.qsize()
                + self.transfer_queue.qsize()
            )
            logger.debug(
                "Released job %s (%s %s). Current queue size: %s",
                job.uuid,
                package.__class__.__name__,
                package.uuid,
                queue_size,
            )

    def await_decision(self, job):
        """Mark a job as awaiting user input to proceed.
        """
        job_id = six.text_type(job.uuid)
        with self.waiting_choices_lock:
            self.waiting_choices[job_id] = job

        self.deactivate_package(job.package)

        if self.debug:
            logger.debug("Marked job %s as awaiting a decision", job.uuid)

    def jobs_awaiting_decisions(self):
        """Returns all jobs waiting for input.
        """
        with self.waiting_choices_lock:
            return self.waiting_choices.copy()

    def decide(self, job_uuid, choice, user_id=None):
        """Make a decsion on a job waiting for user input.
        """
        job_uuid = six.text_type(job_uuid)

        with self.waiting_choices_lock:
            decision = self.waiting_choices[job_uuid]
            # TODO: move this into RPCServer
            decision.set_active_agent(user_id)
            next_job = decision.decide(choice)
            del self.waiting_choices[job_uuid]

        if next_job is not None:
            self.schedule_job(next_job)

        if self.debug:
            logger.debug("Decision made for job %s (%s)", decision.uuid, choice)
