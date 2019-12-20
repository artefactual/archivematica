# -*- coding: utf-8 -*-

# This file is part of Archivematica.
#
# Copyright 2010-2019 Artefactual Systems Inc. <http://artefactual.com>
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

from __future__ import unicode_literals

import os

from components.archival_storage import atom

import metsrw


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(THIS_DIR, "fixtures")


def test__load_premis():
    mw = metsrw.METSDocument.fromfile(os.path.join(FIXTURES_DIR, "mets_two_files.xml"))

    # Load from PREMIS2
    data = {"foo": "bar"}
    atom._load_premis(
        data, mw.get_file(file_uuid="ae8d4290-fe52-4954-b72a-0f591bee2e2f")
    )
    assert data == {
        "foo": "bar",
        "format_name": "JPEG 1.02",
        "format_version": "1.02",
        "format_registry_key": "fmt/44",
        "format_registry_name": "PRONOM",
        "size": "158131",
    }

    # Load from PREMIS3
    data = {"foo": "bar"}
    atom._load_premis(
        data, mw.get_file(file_uuid="4583c44a-046c-4324-9584-345e8b8d82dd")
    )
    assert data == {
        "foo": "bar",
        "format_name": "Format name",
        "format_version": "Format version",
        "format_registry_key": "fmt/12345",
        "format_registry_name": "PRONOM",
        "size": "999999",
    }
