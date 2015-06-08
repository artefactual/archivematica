
import logging

LOGGER = logging.getLogger('archivematica.mcp.server')

def log_exceptions(fn):
    """
    Decorator to wrap a function in a try-catch that logs the exception.

    Useful for catching exceptions in threads, which do not normally report back to the parent thread.
    """
    def wrapped(*args,  **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            LOGGER.exception('Uncaught exception')
            raise
    return wrapped
