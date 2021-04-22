# -*- coding: utf-8 -*-
"""
The PackageQueue class handles job queueing, as it relates to packages.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import functools
import logging
import threading

from django.conf import settings
from django.utils import six
from six.moves import queue as Queue

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

        Enters into an endless loop, pulling jobs from the queue and processing
        them, until `stop` is called.
        """
        while not self.shutdown_event.is_set():
            # Using a timeout here allows shutdown signals to fire
            self.process_one_job(timeout=1.0)

    def process_one_job(self, timeout=None):
        """Process a single job, if one is queued before `timeout`.

        Jobs are submitted to our thread pool. Once the job has done processing
        it will return the next link in the chain, which will be scheduled. Some
        links are terminal, these links indicate the end of the chain for a
        particalar package. If such a link is encountered the package is
        deactivated and the next package is scheduled.
        """
        try:
            job = self.job_queue.get(timeout=timeout)
        except Queue.Empty:
            return

        metrics.job_queue_length_gauge.dec()
        metrics.active_jobs_gauge.inc()

        result = self.executor.submit(job.run)
        result.add_done_callback(self._job_completed_callback)

        if job.link.is_terminal:
            package_done_callback = functools.partial(
                self._package_completed_callback, job.package, job.link.id
            )
            result.add_done_callback(package_done_callback)

        return result

    def stop(self):
        """Trigger queue shutdown."""
        self.shutdown_event.set()

    def _package_completed_callback(self, package, link_id, future):
        """Marks the package as inactive and schedules a new package.

        It is assumed that a package is only complete when a terminal link is
        hit. When we hit a terminal link the future should not contain the next
        job in the chain. This function is called by an executor on completion
        of a Job.
        """
        if future.result() is not None:
            logger.warning(
                "Unexpectedly received another job on package completion. "
                "Please verify the value of `end` in the workflow. Link %s.",
                link_id,
            )
            return

        self.deactivate_package(package)
        self.queue_next_job()

    def _job_completed_callback(self, future):
        """Schedule the next job in the chain.

        Retrieve the next job from the result from the previous job. If there is
        no next_job return, otherwhise schedule the new job. This function is
        called by an executor on completion of a Job.
        """
        metrics.active_jobs_gauge.dec()
        next_job = future.result()

        if not next_job:
            return
        elif isinstance(next_job, DecisionJob) and next_job.awaiting_decision:
            self.await_decision(next_job)
            self.queue_next_job()
        else:
            self.schedule_job(next_job)

    def _put_package_nowait(self, package, job):
        """Queue a package and job for later processing."""
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
        """Mark a package as active, allowing jobs related to it to process."""
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
        """Mark a package as inactive."""
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
        """Mark a job as awaiting user input to proceed."""
        job_id = six.text_type(job.uuid)
        with self.waiting_choices_lock:
            self.waiting_choices[job_id] = job

        self.deactivate_package(job.package)

        if self.debug:
            logger.debug("Marked job %s as awaiting a decision", job.uuid)

    def jobs_awaiting_decisions(self):
        """Returns all jobs waiting for input."""
        with self.waiting_choices_lock:
            return self.waiting_choices.copy()

    def decide(self, job_uuid, choice, user_id=None):
        """Make a decision on a job waiting for user input."""
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
