"""
Main MCPClient entrypoint.
"""

import logging
import os
import pathlib
import signal
from types import FrameType
from typing import Optional

from client import metrics
from client.pool import WorkerPool

logger = logging.getLogger("archivematica.mcp.client")


def main() -> None:
    metrics.start_prometheus_server()

    # Use local XML schemas for validation.
    os.environ["XML_CATALOG_FILES"] = str(
        pathlib.Path(__file__).parent.parent / "assets" / "catalog" / "catalog.xml"
    )

    pool = WorkerPool()
    pool.start()

    def signal_handler(signal: int, frame: Optional[FrameType]) -> None:
        """Used to handle the stop/kill command signals (SIGINT, SIGKILL)."""
        logger.info("Received termination signal (%s)", signal)
        pool.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.pause()  # Wait for exit signal


if __name__ == "__main__":
    main()
