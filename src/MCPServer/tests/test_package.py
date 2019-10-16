from __future__ import absolute_import, division, print_function, unicode_literals

import uuid

import pytest

from main import models

from server.packages import DIP, _determine_transfer_paths


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
        models.SIP.objects.get(uuid=dip.uuid, sip_type="DIP")
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
        models.SIP.objects.get(uuid=dip_uuid, sip_type="DIP")
    except models.SIP.DoesNotExist:
        pytest.fail("DIP.get_or_create_from_db_by_path didn't create a SIP model")
