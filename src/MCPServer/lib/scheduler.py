from __future__ import unicode_literals

import logging
import threading
import Queue

import concurrent.futures


logger = logging.getLogger("archivematica.mcp.server.scheduler")

# TODO: make this better by actually signifying the end of a package in the workflow
PACKAGE_COMPLETED_LINK_IDS = set(
    [
        # Move to SIP Creation
        "d27fd07e-d3ed-4767-96a5-44a2251c6d0a",
        "39a128e3-c35d-40b7-9363-87f75091e1ff",
        # Move to failed directory
        "828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c",
        "377f8ebb-7989-4a68-9361-658079ff8138",
    ]
)
MAX_QUEUED_JOBS = 1024


class PackageScheduler(object):
    """
    Package scheduler/queue.
    """

    def __init__(
        self,
        max_concurrent_packages=2,
        max_queued_packages=MAX_QUEUED_JOBS,
        debug=False,
    ):
        self.max_concurrent_packages = max_concurrent_packages
        self.debug = debug

        self.shutdown_event = threading.Event()
        self.active_package_lock = threading.Lock()
        self.active_packages = {}  # uuid: Package
        self.job_queue = Queue.Queue(maxsize=MAX_QUEUED_JOBS)
        # Split queues by package type
        self.transfer_queue = Queue.Queue(maxsize=max_queued_packages)
        self.sip_queue = Queue.Queue(maxsize=max_queued_packages)
        self.dip_queue = Queue.Queue(maxsize=max_queued_packages)

        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_concurrent_packages
        )

        if self.debug:
            logger.debug("PackageScheduler initalized")

    def schedule_job_chain(self, job_chain):
        # We have many cases where the same package is scheduled again, due to workflow
        # jumps (e.g. moves between watched directories). In that case, just schedule
        # the job immediately.
        package = job_chain.package
        with self.active_package_lock:
            if package.uuid in self.active_packages:
                job = job_chain.get_current_job()
                self.job_queue.put_nowait(job)
                return

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

        self.maybe_process_next_job_chain()

    def schedule_job(self, job):
        with self.active_package_lock:
            if job.package.uuid not in self.active_packages:
                raise ValueError(
                    "Only jobs related to packages currently being processed can be scheduled."
                )

        self.job_queue.put_nowait(job)

    def start(self):
        while not self.shutdown_event.is_set():
            # block until a job is waiting
            job = self.job_queue.get(timeout=None)
            result = self.executor.submit(job.run)
            result.add_done_callback(self.check_package_done)

    def shutdown(self):
        self.shutdown_event.set()
        self.executor.shutdown(wait=True)

    def check_package_done(self, future):
        job = future.result()

        if job.link.id in PACKAGE_COMPLETED_LINK_IDS:
            self.package_done(job.package.uuid)

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
            if self.debug:
                logger.debug("DIP queue empty.")

        try:
            return self.sip_queue.get_nowait()
        except Queue.Empty:
            if self.debug:
                logger.debug("SIP queue empty.")
        try:
            return self.transfer_queue.get_nowait()
        except Queue.Empty:
            if self.debug:
                logger.debug("Transfer queue empty.")

            return None

    def maybe_process_next_job_chain(self):
        # Don't start processing if we're at capacity
        with self.active_package_lock:
            maxed_out = len(self.active_packages) >= self.max_concurrent_packages
            if maxed_out:
                return

        job_chain = self.get_job_chain_nowait()
        if job_chain is None:
            return

        package = job_chain.package
        package_id = str(package.uuid)
        with self.active_package_lock:
            self.active_packages[package_id] = package

        job = job_chain.get_current_job()
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

    def package_done(self, package_id):
        """On package completion, free up the active processing slot.
        """
        package_id = str(package_id)

        with self.active_package_lock:
            del self.active_packages[package_id]

        if self.debug:
            logger.debug("Package %s marked completed", package_id)

        self.maybe_process_next_job_chain()


# global instance, imported elsewhere
package_scheduler = PackageScheduler(debug=True)
