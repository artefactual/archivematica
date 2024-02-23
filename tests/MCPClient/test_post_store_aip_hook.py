import os
from unittest import mock

import post_store_aip_hook
import pytest
from client.job import Job
from django.test import TestCase
from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestDSpaceToArchivesSpace(TestCase):
    """Test sending the DSpace handle to ArchivesSpace."""

    fixture_files = [
        "archivesspaceconfig.json",
        "storageserviceconfig.json",
        "sip.json",
        "archivesspacecomponents.json",
    ]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def setUp(self):
        self.sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"

    def test_no_archivesspace(self):
        """It should abort if no ArchivesSpaceDigitalObject found."""
        models.ArchivesSpaceDigitalObject.objects.all().delete()
        rc = post_store_aip_hook.dspace_handle_to_archivesspace(
            Job("stub", "stub", []), self.sip_uuid
        )
        assert rc == 1

    @mock.patch(
        "storageService.get_file_info",
        return_value=[{"misc_attributes": {}}],
    )
    def test_no_dspace(self, get_file_info):
        """It should abort if no DSpace handle found."""
        rc = post_store_aip_hook.dspace_handle_to_archivesspace(
            Job("stub", "stub", []), self.sip_uuid
        )
        assert rc == 1

    @mock.patch(
        "storageService.get_file_info",
        return_value=[{"misc_attributes": {"handle": "123456789/41"}}],
    )
    @mock.patch(
        "requests.post",
        side_effect=[
            mock.Mock(**{"json.return_value": {"session": "session-id"}}),
            mock.Mock(status_code=200),
        ],
    )
    @mock.patch(
        "requests.get",
        return_value=mock.Mock(
            **{
                "json.return_value": {
                    "file_versions": [
                        {
                            "file_uri": "123456789/41",
                            "use_statement": "text-data",
                            "xlink_actuate_attribute": "none",
                            "xlink_show_attribute": "embed",
                        },
                    ],
                }
            }
        ),
    )
    def test_dspace_handle_to_archivesspace(
        self, requests_get, requests_post, get_file_info
    ):
        """It should send the DSpace handle to ArchivesSpace."""
        rc = post_store_aip_hook.dspace_handle_to_archivesspace(
            Job("stub", "stub", []), self.sip_uuid
        )
        assert rc == 0


@pytest.fixture
def shared_dir(tmp_path):
    result = tmp_path / "sharedDirectory"
    result.mkdir()
    return result


@pytest.fixture
def processing_dir(shared_dir):
    result = shared_dir / "currentlyProcessing"
    result.mkdir()
    return result


@pytest.fixture
def sip(db):
    return models.SIP.objects.create()


@pytest.fixture
def transfer(db, processing_dir):
    transfer_location = processing_dir / "transfer"
    transfer_location.mkdir()
    return models.Transfer.objects.create(currentlocation=str(transfer_location))


@pytest.fixture
def file_(db, sip, transfer):
    return models.File.objects.create(sip=sip, transfer=transfer)


@pytest.fixture
def custom_settings(settings, shared_dir, processing_dir):
    settings.SHARED_DIRECTORY = str(shared_dir)
    settings.PROCESSING_DIRECTORY = str(processing_dir)
    return settings


def test_post_store_hook_deletes_transfer_directory(
    db, mocker, sip, transfer, file_, custom_settings
):
    job = mocker.Mock()

    # The transfer directory exists before calling the delete function
    assert os.path.exists(transfer.currentlocation)

    result = post_store_aip_hook.delete_transfer_directory(job, sip.uuid)

    # The transfer directory is returned and has been deleted
    assert result == transfer.currentlocation
    assert not os.path.exists(transfer.currentlocation)
