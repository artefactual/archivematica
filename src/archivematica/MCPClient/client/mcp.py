"""
Main MCPClient entrypoint.
"""

import importlib.resources
import logging
import os
import signal
from types import FrameType
from typing import Optional

from archivematica.MCPClient.client import metrics
from archivematica.MCPClient.client.pool import WorkerPool

logger = logging.getLogger("archivematica.mcp.client")


def main() -> None:
    metrics.start_prometheus_server()

    # Use local XML schemas for validation.
    existing_catalogs = os.environ.get("XML_CATALOG_FILES", "")
    catalog = str(
        importlib.resources.files("archivematica.MCPClient")
        / "assets"
        / "catalog"
        / "catalog.xml"
    )
    os.environ["XML_CATALOG_FILES"] = (
        f"{catalog} {existing_catalogs}" if existing_catalogs else catalog
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
