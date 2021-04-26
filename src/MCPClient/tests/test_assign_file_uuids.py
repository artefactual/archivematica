import os
import sys

from py.error import EEXIST
import pytest
from six.moves import range

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

from assign_file_uuids import find_mets_file


def touch(path):
    """
    Create a file at a given path (a ``py._path.local.LocalPath``).

    Mimics the Unix command touch: https://en.wikipedia.org/wiki/Touch_(command)
    """
    try:
        path.dirpath().mkdir()
    except EEXIST:
        if path.dirpath().isdir():
            pass
        else:
            raise

    path.write_text(u"Test file created by %s" % __file__, encoding="utf-8")


def test_finds_matching_mets_file(tmpdir):
    touch(tmpdir / "metadata" / "METS.1.xml")
    assert find_mets_file(str(tmpdir)) == str(tmpdir / "metadata" / "METS.1.xml")


def test_ambiguous_mets_file_is_error(tmpdir):
    for i in range(3):
        touch(tmpdir / "metadata" / ("METS.%d.xml" % i))

    with pytest.raises(
        Exception, match="Multiple METS files found in %s/metadata" % tmpdir
    ):
        find_mets_file(str(tmpdir))


def test_no_mets_file_is_error(tmpdir):
    with pytest.raises(Exception, match="No METS file found in %s/metadata" % tmpdir):
        find_mets_file(str(tmpdir))
