import logging
from uuid import UUID

LOGGER = logging.getLogger("archivematica.mcp.server")


def valid_uuid(string):
    """Validate that ``string`` contains a valid UUID, it returns a boolean."""
    try:
        ret = UUID(string, version=4)
    except Exception:
        return False
    return ret.hex == string.replace("-", "")
