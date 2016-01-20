#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import uuid


def valid_uuid(uuid_str):
    if not uuid_str:
        return False
    try:
        uuid.UUID(uuid_str)
    except ValueError:
        return False

    return True


class UUIDArgAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not valid_uuid(values):
            return
        setattr(namespace, self.dest, values)
