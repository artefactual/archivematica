"""The abilities module allows for the description of abilities and their
dependencies across Archivematica components (i.e., dashboard, MCPServer, and
MCPClient).
"""


ABILITIES = (
    # The (elastic)search ability must be enabled in order for Archivematica's
    # transfer backlog to work. Therefore, the "Send to backlog" choice at the
    # "Create SIP(s)" decision point should not be available when the search
    # ability is disabled.
    {
        'name': 'search',
        'enabled_attr': 'SEARCH_ENABLED',
        'dependencies': (
            ('Create SIP(s)', 'Send to backlog'),
        )
    },
)


def choice_is_available(choice, settings):
    """Return ``True`` if the ``MicroServiceChainChoice`` instance ``choice``
    should be presented to the user, given ``ABILITIES`` and the configuration
    object ``settings``.
    """
    for ability in ABILITIES:
        feature_enabled = getattr(settings, ability['enabled_attr'], False)
        if not feature_enabled:
            choice_tuple = (
                choice.choiceavailableatlink.currenttask.description,
                choice.chainavailable.description)
            if choice_tuple in ability['dependencies']:
                return False
    return True
