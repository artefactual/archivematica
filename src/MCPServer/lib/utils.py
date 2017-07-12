import logging

LOGGER = logging.getLogger('archivematica.mcp.server')


def log_exceptions(fn):
    """
    Decorator to wrap a function in a try-catch that logs the exception.

    Useful for catching exceptions in threads, which do not normally report back to the parent thread.
    """
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            LOGGER.exception('Uncaught exception')
            raise
    return wrapped


def isUUID(uuid):
    """Return boolean of whether it's string representation of a UUID v4"""
    split = uuid.split("-")
    if len(split) != 5 \
            or len(split[0]) != 8 \
            or len(split[1]) != 4 \
            or len(split[2]) != 4 \
            or len(split[3]) != 4 \
            or len(split[4]) != 12:
        return False
    return True
