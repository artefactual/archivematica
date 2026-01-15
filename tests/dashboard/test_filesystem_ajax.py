import json
import os
import uuid
from unittest import mock

import pytest
from django.urls import reverse

from archivematica.archivematicaCommon.archivematicaFunctions import b64encode_string
from archivematica.dashboard.components.filesystem_ajax import views
from archivematica.dashboard.main import models


@pytest.mark.django_db
@pytest.mark.parametrize(
    "set_partial_reingest_flag, expected_metadata_dir",
    [
        (False, "metadata"),
        (True, os.path.join("data", "objects", "metadata")),
    ],
    ids=["regular_sip", "partial_reingest"],
)
@mock.patch(
    "archivematica.dashboard.components.filesystem_ajax.views._copy_from_transfer_sources",
    return_value=(None, ""),
)
def test_copy_metadata_files(
    _copy_from_transfer_sources_mock,
    rf,
    set_partial_reingest_flag,
    expected_metadata_dir,
):
    # Create a SIP
    sip_uuid = str(uuid.uuid4())
    sip = models.SIP.objects.create(
        uuid=sip_uuid,
        currentpath=f"%sharedPath%more/path/metadataReminder/mysip-{sip_uuid}/",
    )
    if set_partial_reingest_flag:
        sip.set_partial_reingest()

    # Call the view with a mocked request
    request = rf.post(
        reverse("filesystem_ajax:copy_metadata_files"),
        {
            "sip_uuid": sip_uuid,
            "source_paths[]": [b64encode_string("locationuuid:/some/path")],
        },
    )
    result = views.copy_metadata_files(request)

    # Verify the contents of the response
    assert result.status_code == 201
    assert result["Content-Type"] == "application/json"
    assert json.loads(result.content) == {
        "message": "Metadata files added successfully.",
        "error": None,
    }

    # Verify the copier helper was called with the right parameters
    _copy_from_transfer_sources_mock.assert_called_once_with(
        ["locationuuid:/some/path"],
        f"more/path/metadataReminder/mysip-{sip_uuid}/{expected_metadata_dir}",
    )


def test_contents_sorting(db, tmp_path, admin_client, dashboard_uuid):
    (tmp_path / "1").mkdir()
    (tmp_path / "e").mkdir()
    (tmp_path / "a").mkdir()
    (tmp_path / "0").mkdir()

    response = admin_client.get(
        reverse("filesystem_ajax:contents"), {"path": str(tmp_path)}
    )
    content = json.loads(response.content.decode("utf8"))

    assert [child["name"] for child in content["children"]] == [
        b64encode_string("0"),
        b64encode_string("1"),
        b64encode_string("a"),
        b64encode_string("e"),
    ]
