# -*- coding: utf-8 -*-
"""The abilities module allows for the description of abilities and their
dependencies across Archivematica components (i.e., dashboard, MCPServer, and
MCPClient).
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf import settings


ABILITIES = (
    # The (elastic)search Transfers indexes must be enabled for the transfers
    # backlog. Therefore, the "Send to backlog" choice at the "Create SIP(s)"
    # decision point should not be available when the 'transfers' indexes are
    # not included in the SEARCH_ENABLED setting.
    {
        "name": "search",
        "enabled_attr": "SEARCH_ENABLED",
        "enabled_condition": "in",
        "enabled_value": "transfers",
        "dependencies": (("Create SIP(s)", "Send to backlog"),),
    },
)


def choice_is_available(link, chain):
    """Determine if a choice should be presented to the user.

    Return ``True`` if the ``MicroServiceChainChoice`` instance ``choice``
    should be presented to the user, given ``ABILITIES`` and the configuration
    object ``settings``. If the ability ``enabled_condition`` is set to ``in``,
    check that the ``enabled_value`` is included in the ``enabled_attr`` value.
    Otherwise, check ``enabled_attr`` boolean value.
    """
    for ability in ABILITIES:
        enabled_attr = ability["enabled_attr"]
        if ability["enabled_condition"] == "in":
            attr_value = getattr(settings, enabled_attr, [])
            feature_enabled = ability["enabled_value"] in attr_value
        else:
            feature_enabled = getattr(settings, enabled_attr, False)
        if not feature_enabled:
            choice_tuple = (
                link.get_label("description"),
                chain.get_label("description"),
            )
            if choice_tuple in ability["dependencies"]:
                return False
    return True
