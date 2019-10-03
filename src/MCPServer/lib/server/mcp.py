# -*- coding: utf-8 -*-
"""
Main mcpserver entrypoint.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

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
from server.executor import executor
from server.jobs import Job, JobChain
from server.packages import DIP, Transfer, SIP
from server.queues import PackageQueue
from server.tasks import Task
from server.utils import uuid_from_path
from server.watch_dirs import watch_directories
from server.workflow import load_default_workflow


logger = logging.getLogger("archivematica.mcp.server")

# Tracks whether a sigterm has been received or not
shutdown_event = threading.Event()


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
        uuid = uuid_from_path(path)
        package = Transfer(path, uuid)
    elif package_type == "Transfer" and not is_dir:
        package = Transfer(path, None)
    else:
        raise ValueError("Unexpected unit type given for file {}".format(path))

    job_chain = JobChain(package, watched_dir.chain, watched_dir.chain.workflow)
    package_queue.schedule_job(next(job_chain))


def signal_handler(signal, frame):
    """Used to handle the stop/kill command signals (SIGINT, SIGKILL)"""
    logger.info("Received termination signal (%s)", signal)

    shutdown_event.set()
    executor.shutdown(wait=False)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("This PID: %s", os.getpid())
    logger.info("User: %s", getpass.getuser())

    workflow = load_default_workflow()
    logger.debug("Loaded default workflow.")

    shared_dirs.create()

    Job.cleanup_old_db_entries()
    Task.cleanup_old_db_entries()
    logger.debug("Cleaned up old db entries.")

    metrics.start_prometheus_server()

    package_queue = PackageQueue(executor, shutdown_event, debug=settings.DEBUG)

    rpc_threads = []
    for x in range(settings.RPC_THREADS):
        rpc_thread = threading.Thread(
            target=rpc_server.start,
            args=(workflow, shutdown_event, package_queue),
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

    # Cleanup threads
    watch_dir_thread.join(1.0)
    for thread in rpc_threads:
        thread.join(0.1)
    logger.debug("RPC threads stopped.")

    logger.info("MCP server shut down complete.")


if __name__ == "__main__":
    main()
