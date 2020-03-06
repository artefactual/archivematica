# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import sys
import uuid

import pytest

from main.models import File

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))


from archivematicaCreateMETSReingest import _get_directory_fsentry
from archivematicaCreateMETSReingest import update_metadata_csv


@pytest.fixture
def file_obj(db):
    return File.objects.create(
        uuid=uuid.uuid4(), originallocation="%SIPDirectory%objects/foo.txt"
    )


@pytest.fixture
def mets(mocker, file_obj):
    """Return a mocked metsrw.METSDocument.

    It only implements a get_file method that returns mocked FSEntrys
    for the objects/foo.txt database file and the objects/mydir
    directory.
    """
    aip = mocker.Mock(dmdids=[])
    objects = mocker.Mock(dmdids=[])
    mydir = mocker.Mock(dmdids=[])
    foo = mocker.Mock(dmdids=[])
    # Create a mock directory tree indexed by (parent, label)
    tree = {(None, None): aip, (aip, "objects"): objects, (objects, "mydir"): mydir}

    def get_file_mock(**kwargs):
        file_uuid = kwargs.get("file_uuid")
        if file_uuid is not None and file_uuid == file_obj.uuid:
            return foo
        key = kwargs.get("parent"), kwargs.get("label")
        return tree.get(key)

    return mocker.Mock(
        **{
            "get_file.side_effect": get_file_mock,
            # Mocked directories are attached for convenience
            "aip": aip,
            "objects": objects,
            "mydir": mydir,
            "foo": foo,
        }
    )


def test_get_directory_fsentry(mocker, mets):
    assert _get_directory_fsentry(mets, "nonexistent") is None
    assert _get_directory_fsentry(mets, "objects") is mets.objects
    assert _get_directory_fsentry(mets, "objects/nonexistent") is None
    assert _get_directory_fsentry(mets, "objects/mydir") is mets.mydir
    assert _get_directory_fsentry(mets, "objects/mydir/nonexistent") is None


@pytest.mark.django_db
def test_update_metadata_csv(mocker, file_obj, mets):
    mocker.patch("create_mets_v2.createDmdSecsFromCSVParsedMetadata")
    mocker.patch(
        "archivematicaCreateMETSMetadataCSV.parseMetadataCSV",
        return_value={
            "objects/foo.txt": {"dc.title": "Foo file"},
            "objects/nonexistent.txt": {"dc.title": "Non existent file"},
            "objects/mydir": {"dc.title": "My directory"},
            "objects/mydir/nonexistent": {"dc.title": "Non existent directory"},
        },
    )
    pyprint_mock = mocker.Mock()
    job = mocker.Mock(pyprint=pyprint_mock)
    metadata_csv = mocker.Mock()

    update_metadata_csv(job, mets, metadata_csv, None, None, None)

    # Use the logger to verify what happened
    pyprint_mock.assert_has_calls(
        [
            # Messages for existing database file objects/foo.txt
            mocker.call("Looking for", "objects/foo.txt", "from metadata.csv in SIP"),
            mocker.call("objects/foo.txt", "found in database or METS file"),
            mocker.call("objects/foo.txt", "was associated with", mets.foo.dmdids),
            mocker.call("objects/foo.txt", "now associated with", mets.foo.dmdids),
            # Messages for nonexistent database file
            mocker.call(
                "Looking for", "objects/nonexistent.txt", "from metadata.csv in SIP"
            ),
            mocker.call(
                "objects/nonexistent.txt", "not found in database or METS file"
            ),
            # Messages for existing directory objects/mydir
            mocker.call("Looking for", "objects/mydir", "from metadata.csv in SIP"),
            mocker.call("objects/mydir", "found in database or METS file"),
            mocker.call("objects/mydir", "was associated with", mets.mydir.dmdids),
            mocker.call("objects/mydir", "now associated with", mets.mydir.dmdids),
            # Messages for nonexistent directory objects/mydir/nonexistent
            mocker.call(
                "Looking for", "objects/mydir/nonexistent", "from metadata.csv in SIP"
            ),
            mocker.call(
                "objects/mydir/nonexistent", "not found in database or METS file"
            ),
        ],
        any_order=True,
    )
