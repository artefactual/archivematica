"""
Handle offloading of Task objects to MCP Client for processing.
"""

import threading

from archivematica.MCPServer.server.tasks.backends.base import TaskBackend
from archivematica.MCPServer.server.tasks.backends.gearman_backend import (
    GearmanTaskBackend,
)

backend_local = threading.local()
_backend_generation = 0
_backend_generation_lock = threading.Lock()


def _current_backend_generation():
    with _backend_generation_lock:
        return _backend_generation


def invalidate_task_backends():
    """Arrange for every executor thread to replace its cached backend.

    A thread-local backend can only be shut down safely by its owning thread.
    Advancing a shared generation lets each executor thread discard its own
    connection before it submits its next task.
    """
    global _backend_generation

    with _backend_generation_lock:
        _backend_generation += 1


def get_task_backend():
    """Return the backend for processing tasks.

    The backend is thread-local, so each thread will have a different
    instance.
    """
    # In future, this could be a configuration setting, but for now it
    # is always gearman.
    generation = _current_backend_generation()
    if (
        getattr(backend_local, "task_backend", None) is not None
        and getattr(backend_local, "task_backend_generation", None) != generation
    ):
        reset_task_backend()

    if not getattr(backend_local, "task_backend", None):
        backend_local.task_backend = GearmanTaskBackend()
        backend_local.task_backend_generation = generation

    return backend_local.task_backend


def reset_task_backend():
    """Shut down and forget the backend owned by the current thread."""
    backend = getattr(backend_local, "task_backend", None)
    if backend is None:
        return

    try:
        backend.shutdown()
    finally:
        del backend_local.task_backend
        if hasattr(backend_local, "task_backend_generation"):
            del backend_local.task_backend_generation


__all__ = (
    "GearmanTaskBackend",
    "TaskBackend",
    "get_task_backend",
    "invalidate_task_backends",
    "reset_task_backend",
)
