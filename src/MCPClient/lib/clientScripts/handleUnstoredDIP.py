#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
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

"""Handle Unstored DIP.

This client script hanles an unstored DIP by moving it to the rejected/
directory if it has *not* been uploaded and doing nothing otherwise.
"""
from __future__ import print_function

import os
import sys

import django
django.setup()
# dashboard
from main.models import SIP
# archivematicaCommon
from custom_handlers import get_script_logger


logger = get_script_logger('archivematica.mcp.client.handleUnstoredDIP')


def _sip_uploaded(sip_dir):
    """Return ``True`` if the SIP has been uploaded."""
    return True


def _move_to_rejected(sip_dir, rejected_dir):
    """Move the SIP at ``sip_dir`` to the rejected directory at
    ``rejected_dir``.
    """
    pass


def main(sip_dir, rejected_dir):
    if not _sip_uploaded(sip_dir):
        _move_to_rejected(sip_dir, rejected_dir)
    return 0


if __name__ == '__main__':
    sip_dir, rejected_dir = sys.argv[1:]
    logger.info('handleUnstoredDIP called with sip directory %s and rejected'
                ' directory %s', sip_dir, rejected_dir)
    sys.exit(main(sip_dir, rejected_dir))
