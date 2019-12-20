# -*- coding: utf-8 -*-
"""
Start and run MCPServer via the `main` function.

`main` goes through the following steps:
1. A `ThreadPoolExecutor` is initialized with a configurable number of threads
    (default ncpus).
2. A signal listener is setup to handle shutdown on SIGINT/SIGTERM events.
3. The default workflow is loaded (from workflow.json).
4. The configured SHARED_DIRECTORY is populated with the expected directory
    structure, and default processing configs added.
5. Any in progress Job and Task entries in the database are marked as errors,
    as they are presumed to have been the result of a shutdown while processing.
6. If Prometheus metrics are enabled, an thread is started to serve metrics for
    scraping.
7. A `PackageQueue` (see the `queues` module) is initialized.
8. A configured number (default 4) of RPCServer (see the `rpc_server` module)
    threads are started to handle gearman "RPC" requests from the dashboard.
9. A watched directory thread is started to observe changes in any of the
    watched dirs as set in the workflow.
10. The `PackageQueue.work` processing loop is started on the main thread.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import concurrent.futures
import functools
import getpass
import logging
import os
import signal
import threading

import django

django.setup()

from django.conf import settings

from server import metrics, rpc_server, shared_dirs
from server.jobs import Job, JobChain
from server.packages import DIP, Transfer, SIP
from server.queues import PackageQueue
from server.tasks import Task
from server.watch_dirs import watch_directories
from server.workflow import load_default_workflow


logger = logging.getLogger("archivematica.mcp.server")


def watched_dir_handler(package_queue, path, watched_dir):
    if os.path.isdir(path):
        path = path + "/"
    logger.debug("Starting chain for %s", path)

    package = None
    package_type = watched_dir["unit_type"]
    is_dir = os.path.isdir(path)

    if package_type == "SIP" and is_dir:
        package = SIP.get_or_create_from_db_by_path(path)
    elif package_type == "DIP" and is_dir:
        package = DIP.get_or_create_from_db_by_path(path)
    elif package_type == "Transfer" and is_dir:
        package = Transfer.get_or_create_from_db_by_path(path)
    elif package_type == "Transfer" and not is_dir:
        package = Transfer.get_or_create_from_db_by_path(path)
    else:
        raise ValueError("Unexpected unit type given for file {}".format(path))

    job_chain = JobChain(package, watched_dir.chain, watched_dir.chain.workflow)
    package_queue.schedule_job(next(job_chain))


def main(shutdown_event=None):
    logger.info("This PID: %s", os.getpid())
    logger.info("User: %s", getpass.getuser())

    # Tracks whether a sigterm has been received or not
    if shutdown_event is None:
        shutdown_event = threading.Event()
    executor = concurrent.futures.ThreadPoolExecutor(
        # Lower than the default, since we typically run many processes per system.
        # Defaults to the number of cores available, which is twice as many as the
        # default concurrent packages limit.
        max_workers=settings.WORKER_THREADS
    )

    def signal_handler(signal, frame):
        """Used to handle the stop/kill command signals (SIGINT, SIGKILL)"""
        logger.info("Received termination signal (%s)", signal)

        shutdown_event.set()
        executor.shutdown(wait=False)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    workflow = load_default_workflow()
    logger.debug("Loaded default workflow.")

    shared_dirs.create()

    Job.cleanup_old_db_entries()
    Task.cleanup_old_db_entries()
    logger.debug("Cleaned up old db entries.")

    metrics.init_labels(workflow)
    metrics.start_prometheus_server()

    package_queue = PackageQueue(executor, shutdown_event, debug=settings.DEBUG)

    rpc_threads = []
    for x in range(settings.RPC_THREADS):
        rpc_thread = threading.Thread(
            target=rpc_server.start,
            args=(workflow, shutdown_event, package_queue, executor),
            name="RPCServer-{}".format(x),
        )
        rpc_thread.start()
        rpc_threads.append(rpc_thread)

    watched_dir_callback = functools.partial(watched_dir_handler, package_queue)
    watch_dir_thread = threading.Thread(
        target=watch_directories,
        args=(workflow.get_wdirs(), shutdown_event, watched_dir_callback),
        name="WatchDirs",
    )
    watch_dir_thread.start()

    # Blocks until shutdown_event is set by signal_handler
    package_queue.work()

    # We got a shutdown signal, so cleanup threads
    watch_dir_thread.join(1.0)
    for thread in rpc_threads:
        thread.join(0.1)
    logger.debug("RPC threads stopped.")

    logger.info("MCP server shut down complete.")


if __name__ == "__main__":
    main()
