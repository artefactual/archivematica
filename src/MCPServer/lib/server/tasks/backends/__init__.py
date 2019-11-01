"""
Handle offloading of Task objects to MCP Client for processing.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import threading

from server.tasks.backends.base import TaskBackend
from server.tasks.backends.gearman_backend import GearmanTaskBackend


backend_local = threading.local()


def get_task_backend():
    """Return the backend for processing tasks.

    The backend is thread-local, so each thread will have a different
    instance.
    """
    # In future, this could be a configuration setting, but for now it
    # is always gearman.
    if not getattr(backend_local, "task_backend", None):
        backend_local.task_backend = GearmanTaskBackend()

    return backend_local.task_backend


__all__ = ("GearmanTaskBackend", "TaskBackend", "get_task_backend")
