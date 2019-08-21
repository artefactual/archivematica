# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import threading
import Queue

import concurrent.futures

from django.conf import settings
from django.utils import six


logger = logging.getLogger("archivematica.mcp.server.queues")


class PackageQueue(object):
    """
    Package queue.
    """

    # TODO: make this better by signifying the end of a package in the workflow
    PACKAGE_COMPLETED_LINK_IDS = set(
        [
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
    MAX_QUEUED_PACKAGES = 2048

    def __init__(
        self,
        max_concurrent_packages=settings.CONCURRENT_PACKAGES,
        max_queued_packages=MAX_QUEUED_PACKAGES,
        debug=False,
    ):
        self.max_concurrent_packages = max_concurrent_packages
        self.debug = debug

        self.shutdown_event = threading.Event()
        self.active_package_lock = threading.Lock()
        self.active_packages = {}  # package uuid: Package
        self.job_queue = Queue.Queue(maxsize=max_concurrent_packages)
        # Split queues by package type
        self.transfer_queue = Queue.Queue(maxsize=max_queued_packages)
        self.sip_queue = Queue.Queue(maxsize=max_queued_packages)
        self.dip_queue = Queue.Queue(maxsize=max_queued_packages)

        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_concurrent_packages
        )

        if self.debug:
            logger.debug("%s initialized", self.__class__.__name__)

    def schedule_job_chain(self, job_chain):
        # We have many cases where the same package is scheduled again, due to workflow
        # jumps (e.g. moves between watched directories). In that case, just schedule
        # the job immediately, so we don't jump between packages too much.
        package = job_chain.package
        with self.active_package_lock:
            if package.uuid in self.active_packages:
                job = next(job_chain)
                try:
                    self.job_queue.put_nowait(job)
                except Queue.Full:
                    # Reset the chain for normal queueing
                    job_chain.reset()
                else:
                    # no further action needed
                    return

            active_package_count = len(self.active_packages)

        self.put_job_chain_nowait(job_chain)

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
                "Scheduled job chain %s (%s %s). Current queue size: %s",
                job_chain.id,
                package.__class__.__name__,
                package.uuid,
                queue_size,
            )

        # Don't start processing unless we have capacity
        if active_package_count < self.max_concurrent_packages:
            self.process_next_job_chain()
        elif self.debug:
            logger.debug(
                "Not processing next job chain; %s packages already active",
                active_package_count,
            )

    def schedule_job(self, job):
        with self.active_package_lock:
            if job.package.uuid not in self.active_packages:
                raise ValueError(
                    "Only jobs related to packages currently being processed can be scheduled."
                )

        self.job_queue.put_nowait(job)

    def process(self):
        while not self.shutdown_event.is_set():
            # block until a job is waiting
            job = self.job_queue.get(timeout=None)
            result = self.executor.submit(job.run)
            result.add_done_callback(self.handle_job_complete)

    def stop(self):
        self.shutdown_event.set()
        self.executor.shutdown(wait=True)

    def handle_job_complete(self, future):
        job = future.result()

        try:
            next_job = next(job.job_chain)
        except StopIteration:
            next_job = None
        else:
            self.schedule_job(next_job)

        if next_job is None and job.link.id in self.PACKAGE_COMPLETED_LINK_IDS:
            with self.active_package_lock:
                del self.active_packages[job.package.uuid]

            if self.debug:
                logger.debug("Package %s marked completed", job.package.uuid)

            self.process_next_job_chain()

    def put_job_chain_nowait(self, job_chain):
        # TODO: switch on class type?
        if job_chain.package.UNIT_VARIABLE_TYPE == "DIP":
            self.dip_queue.put_nowait(job_chain)
        elif job_chain.package.UNIT_VARIABLE_TYPE == "SIP":
            self.sip_queue.put_nowait(job_chain)
        else:
            self.transfer_queue.put_nowait(job_chain)

    def get_job_chain_nowait(self):
        """Return the next job chain, prioritizing by package type.
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

    def process_next_job_chain(self):
        job_chain = self.get_job_chain_nowait()
        if job_chain is None:
            return  # nothing to do

        package = job_chain.package
        with self.active_package_lock:
            self.active_packages[package.uuid] = package

        job = next(job_chain)
        self.job_queue.put_nowait(job)

        if self.debug:
            queue_size = (
                self.sip_queue.qsize()
                + self.dip_queue.qsize()
                + self.transfer_queue.qsize()
            )
            logger.debug(
                "Released job chain %s (%s %s). Current queue size: %s",
                job_chain.id,
                package.__class__.__name__,
                package.uuid,
                queue_size,
            )


class DecisionQueue(object):
    """Handles jobs awaiting user decisions.
    """

    def __init__(self, package_queue):
        self.package_queue = package_queue
        self.lock = threading.Lock()
        self.waiting_choices = {}  # job.uuid: WorkflowDecision

    def put(self, job, decision):
        job_id = six.text_type(job.uuid)
        with self.lock:
            self.waiting_choices[job_id] = decision

    def all(self):
        with self.lock:
            return self.waiting_choices.copy()

    def decide(self, job_uuid, choice, user_id=None):
        job_uuid = six.text_type(job_uuid)

        with self.lock:
            decision = self.self.waiting_choices[job_uuid]
            next_chain = decision.decide(choice, user_id=user_id)
            del self.waiting_choices[job_uuid]

        if next_chain is not None:
            self.package_queue.schedule_job_chain(next_chain)


# Shared globals
# TODO: remove, and pass these where required.
package_queue = PackageQueue(debug=False)
decision_queue = DecisionQueue(package_queue)
