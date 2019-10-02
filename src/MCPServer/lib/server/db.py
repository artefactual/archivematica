# -*- coding: utf-8 -*-
"""
Database related functionality.

This module implements an `auto_close_old_connections` decorator/context manager.
In order to be able to re-use database connections in the Django ORM outside of
the typical request/response cycle, we have to wrap database usage in order to
make sure anything older than CONN_MAX_AGE is cleared.

This is done via the function decorator `auto_close_old_connections()` in most
cases. For some cases (e.g. generator functions) it may be preferable to use it
as a context manager. Note that because of multiple entry points we sometimes
end up entering multiple times; that causes a slight increase in overhead, but
it is much preferred to having an unwrapped function, which may cause errors.

To debug connection timeouts, turn DEBUG on in Django settings, which will log
all SQL queries and allow us to check that all logged queries occur within the
wrapper. Note though, this will result in _very_ verbose logs.
"""


from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import threading
import traceback

try:
    from contextlib import ContextDecorator
except ImportError:
    from contextdecorator import ContextDecorator  # py2 backport

from django.conf import settings
from django.db import close_old_connections


logger = logging.getLogger("archivematica.mcp.server.db")
thread_locals = threading.local()


class AutoCloseOldConnections(ContextDecorator):
    """
    Decorator to ensure that db connections older than CONN_MAX_AGE are
    closed before execution. Normally, one would close connections after
    execution, but we have some jobs that could run for hours out of
    process, then trigger db access.
    """

    def __enter__(self):
        close_old_connections()
        return self

    def __exit__(self, *exc):
        return False


class DebugAutoCloseOldConnections(AutoCloseOldConnections):
    """
    Debug version of AutoCloseOldConnections; logs warnings with stack traces
    to identify functions that should be wrapped.
    """

    def __enter__(self):
        if not hasattr(thread_locals, "auto_close_connections_depth"):
            thread_locals.auto_close_connections_depth = 0
        thread_locals.auto_close_connections_depth += 1
        logger.debug(
            "Entered auto close connections (depth %s)",
            thread_locals.auto_close_connections_depth,
        )
        return super(DebugAutoCloseOldConnections, self).__enter__()

    def __exit__(self, *exc):
        thread_locals.auto_close_connections_depth -= 1
        logger.debug(
            "Exited auto close connections (depth %s)",
            thread_locals.auto_close_connections_depth,
        )
        return False


class CheckCloseConnectionsHandler(logging.Handler):
    """A logger that issues warnings when the database is accessed outside
    of an auto_close_old_connections wrapper.
    """

    def emit(self, record):
        if getattr(thread_locals, "auto_close_connections_depth", 0) <= 0:
            logger.warning(
                "Database access occurred outside of an "
                "auto_close_old_connections context. Traceback: %s",
                "\n".join(traceback.format_stack()),
            )


if settings.DEBUG:
    logger.debug("Using DEBUG auto_close_old_connections")
    auto_close_old_connections = DebugAutoCloseOldConnections

    # Queries are  only logged if DEBUG is on.
    db_logger = logging.getLogger("django.db.backends")
    db_logger.setLevel(logging.DEBUG)
    handler = CheckCloseConnectionsHandler(level=logging.DEBUG)
    db_logger.addHandler(handler)
else:
    auto_close_old_connections = AutoCloseOldConnections


__all__ = ("auto_close_old_connections",)
