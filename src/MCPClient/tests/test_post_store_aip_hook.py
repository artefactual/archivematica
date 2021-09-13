# -*- coding: utf8
import os

import vcr

from django.test import TestCase
import pytest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
import post_store_aip_hook
from client.job import Job

from main import models

my_vcr = vcr.VCR(
    cassette_library_dir=os.path.join(THIS_DIR, "fixtures", "vcr_cassettes"),
    path_transformer=vcr.VCR.ensure_suffix(".yaml"),
)


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

    def test_no_dspace(self):
        """It should abort if no DSpace handle found."""
        with my_vcr.use_cassette("test_no_dspace.yaml") as c:
            rc = post_store_aip_hook.dspace_handle_to_archivesspace(
                Job("stub", "stub", []), self.sip_uuid
            )
            assert rc == 1
            assert c.all_played

    def test_dspace_handle_to_archivesspace(self):
        """It should send the DSpace handle to ArchivesSpace."""
        with my_vcr.use_cassette("test_dspace_handle_to_archivesspace.yaml") as c:
            rc = post_store_aip_hook.dspace_handle_to_archivesspace(
                Job("stub", "stub", []), self.sip_uuid
            )
            assert rc == 0
            assert c.all_played


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
