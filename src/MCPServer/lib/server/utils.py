# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import uuid


def uuid_from_path(path):
    uuid_in_path = path[-37:-1]
    try:
        return uuid.UUID(uuid_in_path)
    except ValueError:
        return None
