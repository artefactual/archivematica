# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import functools
import logging
import threading
import Queue

from django.conf import settings
from django.utils import six

from server.jobs import DecisionJob
from server.packages import DIP, SIP


logger = logging.getLogger("archivematica.mcp.server.queues")


class PackageQueue(object):
    """Package queue

    This queue throttles `Job` objects belonging to packages, so that at most
    `CONCURRENT_PACKAGES` are active at any one time.

    It also tracks any jobs waiting for decisions in memory. This is a bit of
    a separate concern from package queuing and could be isolated in future.

    Methods on this class should be threadsafe.
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
            logger.debug("%s initialized", self.__class__.__name__)

    def schedule_job(self, job):
        """Add a job to the queue.

        If the Job's package is currently "active", it will be added to the
        queue for immediate processing. Otherwise, it will be added to the
        package queue.
        """

        if self.shutdown_event.is_set():
            raise RuntimeError("Queue stopped.")

        # The most common case is an already active package is scheduled
        package = job.package
        with self.active_package_lock:
            if package.uuid in self.active_packages:
                # If there's no slot available, block until ready
                self.job_queue.put(job, block=True)
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
        """Enter into an endless loop, pulling jobs from the queue and processing them,
        until `stop` is called.
        """
        while not self.shutdown_event.is_set():
            # block until a job is waiting
            job = self.job_queue.get(timeout=None)
            result = self.executor.submit(job.run)
            result.add_done_callback(self._job_completed_callback)

            if job.link.id in self.PACKAGE_COMPLETED_LINK_IDS:
                package_done_callback = functools.partial(
                    self._package_completed_callback, job.package
                )
                result.add_done_callback(package_done_callback)

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
        next_job = future.result()

        if not next_job:
            return

        if isinstance(next_job, DecisionJob) and next_job.awaiting_decision:
            self.await_decision(next_job)
        else:
            self.schedule_job(next_job)

    def _put_package_nowait(self, package, job):
        """Queue a package for processing when one of the currently active
        packages finishes.
        """
        if isinstance(package, DIP):
            self.dip_queue.put_nowait(job)
        elif isinstance(package, SIP):
            self.sip_queue.put_nowait(job)
        else:
            self.transfer_queue.put_nowait(job)

    def _get_package_job_nowait(self):
        """Return the next job, prioritizing by package type.
        """
        try:
            return self.dip_queue.get_nowait()
        except Queue.Empty:
            pass

        try:
            return self.sip_queue.get_nowait()
        except Queue.Empty:
            pass

        try:
            return self.transfer_queue.get_nowait()
        except Queue.Empty:
            pass

        return None

    def activate_package(self, package):
        """Mark a package as active, allowing jobs related to it to process.
        """
        with self.active_package_lock:
            self.active_packages[package.uuid] = package

        if self.debug:
            logger.debug("Marked package %s as active", package.uuid)

    def deactivate_package(self, package):
        """Mark a package as inactive.
        """
        with self.active_package_lock:
            del self.active_packages[package.uuid]

        if self.debug:
            logger.debug("Marked package %s as inactive", package.uuid)

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

        if self.debug:
            queue_size = (
                self.sip_queue.qsize()
                + self.dip_queue.qsize()
                + self.transfer_queue.qsize()
            )
            logger.debug(
                "Released job job %s (%s %s). Current queue size: %s",
                job.id,
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

        self.schedule_job(next_job)
