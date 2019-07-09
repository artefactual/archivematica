from __future__ import absolute_import, division, print_function, unicode_literals

import uuid

import pytest

from main import models

from server.packages import (
    DIP,
    _determine_transfer_paths,
    _move_to_internal_shared_dir,
    _pad_destination_filepath_if_it_already_exists,
)

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


@pytest.mark.parametrize(
    "name,path,tmpdir,expected",
    [
        (
            "TransferName",
            "a00a29b6-7530-4f09-b3df-fd88d9e478b1:home/username/archive.zip",
            "/tmp/tmp.WXA9V7LCy1",
            (
                # copy_to
                "/tmp/tmp.WXA9V7LCy1",
                # final_location
                "/tmp/tmp.WXA9V7LCy1/archive.zip",
                # copy_from
                "a00a29b6-7530-4f09-b3df-fd88d9e478b1:home/username/archive.zip",
            ),
        ),
        (
            "TransferName",
            "a00a29b6-7530-4f09-b3df-fd88d9e478b2:home/username/dir",
            "/tmp/tmp.WXA9V7LCy2",
            (
                # copy_to
                "/tmp/tmp.WXA9V7LCy2/TransferName",
                # final_location
                "/tmp/tmp.WXA9V7LCy2/TransferName",
                # copy_from
                "a00a29b6-7530-4f09-b3df-fd88d9e478b2:home/username/dir/.",
            ),
        ),
    ],
)
@pytest.mark.django_db
def test__determine_transfer_paths(name, path, tmpdir, expected):
    results = _determine_transfer_paths(name, path, tmpdir)
    assert results[0] == expected[0], "name mismatch"
    assert results[1] == expected[1], "path mismatch"
    assert results[2] == expected[2], "tmpdir mismatch"


@pytest.mark.django_db(transaction=True)
def test_dip_get_or_create_from_db_path_without_uuid(tmp_path):
    dip_path = tmp_path / "test-dip"

    dip = DIP.get_or_create_from_db_by_path(str(dip_path))

    assert dip.current_path == str(dip_path)
    try:
        models.SIP.objects.get(uuid=dip.uuid)
    except models.SIP.DoesNotExist:
        pytest.fail("DIP.get_or_create_from_db_by_path didn't create a SIP model")


@pytest.mark.django_db(transaction=True)
def test_dip_get_or_create_from_db_path_with_uuid(tmp_path):
    dip_uuid = uuid.uuid4()
    dip_path = tmp_path / "test-dip-{}".format(dip_uuid)

    dip = DIP.get_or_create_from_db_by_path(str(dip_path))

    assert dip.uuid == dip_uuid
    assert dip.current_path == str(dip_path)
    try:
        models.SIP.objects.get(uuid=dip_uuid)
    except models.SIP.DoesNotExist:
        pytest.fail("DIP.get_or_create_from_db_by_path didn't create a SIP model")


class TestPadDestinationFilePath:
    def test_zipfile_is_not_padded_if_does_not_exist(self, tmp_path):
        transfer_path = tmp_path / "transfer.zip"
        padded_path = _pad_destination_filepath_if_it_already_exists(transfer_path)
        assert padded_path == transfer_path

    def test_zipfile_is_padded_if_exists(self, tmp_path):
        transfer_path = tmp_path / "transfer.zip"
        transfer_path.touch()
        padded_path = _pad_destination_filepath_if_it_already_exists(transfer_path)
        assert padded_path == tmp_path / "transfer_1.zip"

    def test_dir_is_not_padded_if_does_not_exist(self, tmp_path):
        transfer_path = tmp_path / "transfer/"
        padded_path = _pad_destination_filepath_if_it_already_exists(transfer_path)
        assert padded_path == transfer_path

    def test_dir_is_padded_if_exists(self, tmp_path):
        transfer_path = tmp_path / "transfer/"
        transfer_path.mkdir()
        padded_path = _pad_destination_filepath_if_it_already_exists(transfer_path)
        assert padded_path == tmp_path / "transfer_1"


@pytest.fixture
def transfer():
    return models.Transfer.objects.create()


@pytest.fixture
def processing_dir(tmp_path):
    proc_dir = tmp_path / "processing"
    proc_dir.mkdir()
    return proc_dir


@pytest.mark.django_db(transaction=True)
class TestMoveToInternalSharedDir:
    def test_move_dir(self, tmp_path, processing_dir, transfer):
        filepath = tmp_path / "transfer"
        filepath.mkdir()

        _move_to_internal_shared_dir(str(filepath), str(processing_dir), transfer)

        transfer.refresh_from_db()
        dest_path = processing_dir / "transfer"
        assert dest_path.is_dir()
        assert Path(transfer.currentlocation) == dest_path

    def test_move_file(self, tmp_path, processing_dir, transfer):
        filepath = tmp_path / "transfer.zip"
        filepath.touch()

        _move_to_internal_shared_dir(str(filepath), str(processing_dir), transfer)

        dest_path = processing_dir / "transfer.zip"
        assert dest_path.is_file()
        assert (processing_dir / "transfer").is_dir()

        transfer.refresh_from_db()
        assert Path(transfer.currentlocation) == dest_path

    def test_move_processing_config_with_zipfile(
        self, tmp_path, processing_dir, transfer
    ):
        filepath = tmp_path / "transfer.zip"
        filepath.touch()

        config = tmp_path / "processingMCP.xml"
        config.touch()

        _move_to_internal_shared_dir(str(filepath), str(processing_dir), transfer)

        config_dest = processing_dir / "transfer/processingMCP.xml"
        assert config_dest.is_file()
