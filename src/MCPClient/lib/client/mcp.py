"""
Main MCPClient entrypoint.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import multiprocessing
import signal

from client import metrics
from client.pool import WorkerPool


logger = logging.getLogger("archivematica.mcp.client")


def main():
    metrics.start_prometheus_server()

    pool = WorkerPool(multiprocessing.cpu_count())
    pool.start()

    def signal_handler(signal, frame):
        """Used to handle the stop/kill command signals (SIGINT, SIGKILL)"""
        logger.info("Received termination signal (%s)", signal)
        pool.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Wait for exit signal
    signal.pause()


if __name__ == "__main__":
    main()
