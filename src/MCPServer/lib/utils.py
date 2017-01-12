import logging
import string

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


def get_decimal_date(date):
    valid = "." + string.digits
    ret = ""
    for c in date:
        if c in valid:
            ret += c
    return str("{:10.10f}".format(float(ret)))


def is_uuid(uuid):
    """
    Return boolean of whether it's string representation of a UUID v4.
    """
    split = uuid.split('-')
    if len(split) != 5 or len(split[0]) != 8 or len(split[1]) != 4 or len(split[2]) != 4 or len(split[3]) != 4 or len(split[4]) != 12:
        return False
    return True


def get_uuid_from_path(path):
    """
    Find UUID on end of SIP path.
    """
    uuidLen = -36
    if is_uuid(path[uuidLen - 1:-1]):
        return path[uuidLen - 1:-1]
