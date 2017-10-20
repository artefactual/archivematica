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


# Maps decision point UUIDs and decision UUIDs to their "canonical"
# equivalents. This is useful for when there are multiple decision points which
# are effectively identical and a preconfigured decision for one should hold for
# all of the others as well. For example, there are 5 "Assign UUIDs to
# directories?" decision points and making a processing config decision for the
# designated canonical one, in this case
# 'bd899573-694e-4d33-8c9b-df0af802437d', should result in that decision taking
# effect for all of the others as well. This allows that. See
# linkTaskManagerReplacementDicFromChoice.py.
choice_unifier = {
    # Decision point "Assign UUIDs to directories?"
    '8882bad4-561c-4126-89c9-f7f0c083d5d7': 'bd899573-694e-4d33-8c9b-df0af802437d',
    'e10a31c3-56df-4986-af7e-2794ddfe8686': 'bd899573-694e-4d33-8c9b-df0af802437d',
    'd6f6f5db-4cc2-4652-9283-9ec6a6d181e5': 'bd899573-694e-4d33-8c9b-df0af802437d',
    '1563f22f-f5f7-4dfe-a926-6ab50d408832': 'bd899573-694e-4d33-8c9b-df0af802437d',

    # Decision "Yes" (for "Assign UUIDs to directories?")
    '7e4cf404-e62d-4dc2-8d81-6141e390f66f': '2dc3f487-e4b0-4e07-a4b3-6216ed24ca14',
    '2732a043-b197-4cbc-81ab-4e2bee9b74d3': '2dc3f487-e4b0-4e07-a4b3-6216ed24ca14',
    'aa793efa-1b62-498c-8f92-cab187a99a2a': '2dc3f487-e4b0-4e07-a4b3-6216ed24ca14',
    'efd98ddb-80a6-4206-80bf-81bf00f84416': '2dc3f487-e4b0-4e07-a4b3-6216ed24ca14',

    # Decision "No" (for "Assign UUIDs to directories?")
    '0053c670-3e61-4a3e-a188-3a2dd1eda426': '891f60d0-1ba8-48d3-b39e-dd0934635d29',
    '8e93e523-86bb-47e1-a03a-4b33e13f8c5e': '891f60d0-1ba8-48d3-b39e-dd0934635d29',
    '6dfbeff8-c6b1-435b-833a-ed764229d413': '891f60d0-1ba8-48d3-b39e-dd0934635d29',
    'dc0ee6b6-ed5f-42a3-bc8f-c9c7ead03ed1': '891f60d0-1ba8-48d3-b39e-dd0934635d29',
}
