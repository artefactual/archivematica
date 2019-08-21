# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import functools

from django.db import close_old_connections


def auto_close_old_connections(func):
    """
    Decorator to ensure that db connections older than CONN_MAX_AGE are
    closed before execution. Normally, one would close connections after
    execution, but we have some jobs that could run for hours out of
    process, then trigger db access.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        close_old_connections()
        return func(*args, **kwargs)

    return wrapper
