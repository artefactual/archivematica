"""
Utility functions.
"""
import uuid


def uuid_from_path(path):
    uuid_in_path = path.rstrip("/")[-36:]
    try:
        return uuid.UUID(uuid_in_path)
    except ValueError:
        return None
