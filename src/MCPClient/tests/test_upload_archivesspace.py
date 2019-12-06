"""Tests for the upload_archivesspace.py client script."""

import os
import sys

import pytest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

import upload_archivesspace


def test_recursive_file_gen(tmpdir):
    mydir = tmpdir.mkdir("mydir")
    hello = mydir.join("hello.txt")
    hello.write("hello!")
    bye = mydir.mkdir("sub").join("bye.txt")
    bye.write("bye!")
    result = list(upload_archivesspace.recursive_file_gen(str(mydir)))
    assert sorted(result) == [str(hello), str(bye)]


def test_get_files_from_dip_finds_files(tmpdir):
    dip = tmpdir.mkdir("mydip")
    objects = dip.mkdir("objects")
    object1 = objects.join("object1.txt")
    object1.write("object 1")
    object2 = objects.mkdir("subdir").join("object2.txt")
    object2.write("object 2")
    # TODO:
    # - use os.path.join in the function and make trailing slash optional
    # - remove last two parameters, they're not used in the function
    result = upload_archivesspace.get_files_from_dip(str(dip) + "/", None, None)
    assert sorted(result) == [str(object1), str(object2)]


def test_get_files_from_dip_with_empty_dip_location(tmpdir, mocker):
    logger = mocker.patch("upload_archivesspace.logger")
    dip = tmpdir.mkdir("mydip")
    with pytest.raises(ValueError) as excinfo:
        upload_archivesspace.get_files_from_dip(str(dip) + "/", None, None)
    assert excinfo.value.message == "cannot find dip"
    logger.error.assert_called_once_with("no files in {}/objects/".format(str(dip)))


def test_get_pairs(mocker):
    dip_uuid = "somedipuuid"
    filter_mock = mocker.patch(
        "upload_archivesspace.ArchivesSpaceDIPObjectResourcePairing.objects.filter",
        return_value=[
            mocker.Mock(fileuuid="1", resourceid="myresource"),
            mocker.Mock(fileuuid="2", resourceid="myresource"),
        ],
    )
    result = upload_archivesspace.get_pairs(dip_uuid)
    assert result == {"1": "myresource", "2": "myresource"}
    filter_mock.assert_called_once_with(dipuuid=dip_uuid)


def test_delete_pairs(mocker):
    dip_uuid = "somedipuuid"
    queryset_mock = mocker.Mock()
    filter_mock = mocker.patch(
        "upload_archivesspace.ArchivesSpaceDIPObjectResourcePairing.objects.filter",
        return_value=queryset_mock,
    )
    upload_archivesspace.delete_pairs(dip_uuid)
    filter_mock.assert_called_once_with(dipuuid=dip_uuid)
    queryset_mock.delete.assert_called_once()
