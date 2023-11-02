import os

import pytest
from django.test import TestCase
from requests_mock import Mocker

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
import post_store_aip_hook
from job import Job

from main import models


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

    @Mocker()
    def test_no_dspace(self, requests_mock):
        """It should abort if no DSpace handle found."""
        requests_mock.get(
            "http://localhost:8000/api/v2/file/?uuid=4060ee97-9c3f-4822-afaf-ebdf838284c3&offset=0",
            json={
                "meta": {
                    "limit": 20,
                    "next": None,
                    "offset": 0,
                    "previous": None,
                    "total_count": 1,
                },
                "objects": [
                    {
                        "current_full_path": "http:/dspace5x.archivematica.org:8080/swordv2/collection/123456789/2/http:/dspace5x.archivematica.org:8080/swordv2/statement/92.atom",
                        "current_location": "/api/v2/location/758cf517-45f7-4c78-8074-32c686c653cb/",
                        "current_path": "http://dspace5x.archivematica.org:8080/swordv2/statement/92.atom",
                        "misc_attributes": {},
                        "origin_pipeline": "/api/v2/pipeline/32836b5b-950e-4409-a823-830d2dd01026/",
                        "package_type": "AIP",
                        "related_packages": [],
                        "resource_uri": "/api/v2/file/4060ee97-9c3f-4822-afaf-ebdf838284c3/",
                        "size": 21244662,
                        "status": "UPLOADED",
                        "uuid": "4060ee97-9c3f-4822-afaf-ebdf838284c3",
                    }
                ],
            },
        )
        rc = post_store_aip_hook.dspace_handle_to_archivesspace(
            Job("stub", "stub", []), self.sip_uuid
        )
        assert rc == 1

    @Mocker()
    def test_dspace_handle_to_archivesspace(self, requests_mock):
        """It should send the DSpace handle to ArchivesSpace."""
        requests_mock.get(
            "http://localhost:8000/api/v2/file/?uuid=4060ee97-9c3f-4822-afaf-ebdf838284c3&offset=0",
            json={
                "meta": {
                    "limit": 20,
                    "next": None,
                    "offset": 0,
                    "previous": None,
                    "total_count": 1,
                },
                "objects": [
                    {
                        "current_full_path": "http:/dspace5x.archivematica.org:8080/swordv2/collection/123456789/2/http:/dspace5x.archivematica.org:8080/swordv2/statement/92.atom",
                        "current_location": "/api/v2/location/758cf517-45f7-4c78-8074-32c686c653cb/",
                        "current_path": "http://dspace5x.archivematica.org:8080/swordv2/statement/92.atom",
                        "misc_attributes": {"handle": "123456789/41"},
                        "origin_pipeline": "/api/v2/pipeline/32836b5b-950e-4409-a823-830d2dd01026/",
                        "package_type": "AIP",
                        "related_packages": [],
                        "resource_uri": "/api/v2/file/4060ee97-9c3f-4822-afaf-ebdf838284c3/",
                        "size": 21244662,
                        "status": "UPLOADED",
                        "uuid": "4060ee97-9c3f-4822-afaf-ebdf838284c3",
                    }
                ],
            },
        )
        requests_mock.post(
            "http://localhost:8089/users/admin/login?password=admin",
            json={
                "session": "57823397705778ab52fea1cbb1a690c46218dfb0277ed021f496849dc328d37b",
                "user": {
                    "lock_version": 6298,
                    "username": "admin",
                    "name": "Administrator",
                    "is_system_user": True,
                    "create_time": "2015-09-22T18:46:11Z",
                    "system_mtime": "2016-09-20T23:11:32Z",
                    "user_mtime": "2016-09-20T23:11:32Z",
                    "jsonmodel_type": "user",
                    "groups": [],
                    "is_admin": True,
                    "uri": "/users/1",
                    "agent_record": {"ref": "/agents/people/1"},
                    "permissions": {
                        "/repositories/1": [
                            "update_location_record",
                            "delete_vocabulary_record",
                            "update_subject_record",
                            "delete_subject_record",
                            "update_agent_record",
                            "delete_agent_record",
                            "update_vocabulary_record",
                            "merge_subject_record",
                            "merge_agent_record",
                            "system_config",
                            "administer_system",
                            "manage_users",
                            "become_user",
                            "view_all_records",
                            "create_repository",
                            "delete_repository",
                            "transfer_repository",
                            "index_system",
                            "manage_repository",
                            "update_accession_record",
                            "update_resource_record",
                            "update_digital_object_record",
                            "update_event_record",
                            "delete_event_record",
                            "suppress_archival_record",
                            "transfer_archival_record",
                            "delete_archival_record",
                            "view_suppressed",
                            "view_repository",
                            "update_classification_record",
                            "delete_classification_record",
                            "mediate_edits",
                            "import_records",
                            "cancel_importer_job",
                            "manage_subject_record",
                            "manage_agent_record",
                            "manage_vocabulary_record",
                            "merge_agents_and_subjects",
                            "merge_archival_record",
                            "manage_rde_templates",
                        ],
                        "_archivesspace": [
                            "system_config",
                            "administer_system",
                            "manage_users",
                            "become_user",
                            "view_all_records",
                            "create_repository",
                            "delete_repository",
                            "transfer_repository",
                            "index_system",
                            "manage_repository",
                            "update_accession_record",
                            "update_resource_record",
                            "update_digital_object_record",
                            "update_event_record",
                            "delete_event_record",
                            "suppress_archival_record",
                            "transfer_archival_record",
                            "delete_archival_record",
                            "view_suppressed",
                            "view_repository",
                            "update_classification_record",
                            "delete_classification_record",
                            "mediate_edits",
                            "import_records",
                            "cancel_importer_job",
                            "manage_subject_record",
                            "manage_agent_record",
                            "manage_vocabulary_record",
                            "merge_agents_and_subjects",
                            "merge_archival_record",
                            "manage_rde_templates",
                            "update_location_record",
                            "delete_vocabulary_record",
                            "update_subject_record",
                            "delete_subject_record",
                            "update_agent_record",
                            "delete_agent_record",
                            "update_vocabulary_record",
                            "merge_subject_record",
                            "merge_agent_record",
                        ],
                    },
                },
            },
        )
        requests_mock.get(
            "http://localhost:8089/repositories/2/digital_objects/211",
            json={
                "lock_version": 4,
                "digital_object_id": "ac256851-ba50-4c99-a488-25fa442ed242",
                "title": "misty-test-1",
                "publish": False,
                "restrictions": False,
                "created_by": "admin",
                "last_modified_by": "admin",
                "create_time": "2016-09-20T18:22:56Z",
                "system_mtime": "2016-09-20T18:48:06Z",
                "user_mtime": "2016-09-20T18:48:06Z",
                "suppressed": False,
                "digital_object_type": "text",
                "jsonmodel_type": "digital_object",
                "external_ids": [],
                "subjects": [],
                "linked_events": [],
                "extents": [],
                "dates": [],
                "external_documents": [],
                "rights_statements": [],
                "linked_agents": [],
                "file_versions": [
                    {
                        "lock_version": 0,
                        "file_uri": "123456789/41",
                        "created_by": "admin",
                        "last_modified_by": "admin",
                        "create_time": "2016-09-20T18:48:06Z",
                        "system_mtime": "2016-09-20T18:48:06Z",
                        "user_mtime": "2016-09-20T18:48:06Z",
                        "use_statement": "text-data",
                        "xlink_actuate_attribute": "none",
                        "xlink_show_attribute": "embed",
                        "jsonmodel_type": "file_version",
                        "identifier": "289",
                    },
                    {
                        "lock_version": 0,
                        "file_uri": "123456789/41",
                        "created_by": "admin",
                        "last_modified_by": "admin",
                        "create_time": "2016-09-20T18:48:06Z",
                        "system_mtime": "2016-09-20T18:48:06Z",
                        "user_mtime": "2016-09-20T18:48:06Z",
                        "use_statement": "text-data",
                        "xlink_actuate_attribute": "none",
                        "xlink_show_attribute": "embed",
                        "jsonmodel_type": "file_version",
                        "identifier": "290",
                    },
                ],
                "notes": [],
                "linked_instances": [{"ref": "/repositories/2/archival_objects/8887"}],
                "uri": "/repositories/2/digital_objects/211",
                "repository": {"ref": "/repositories/2"},
                "tree": {"ref": "/repositories/2/digital_objects/211/tree"},
            },
        )
        requests_mock.post(
            "http://localhost:8089/repositories/2/digital_objects/211",
            json={
                "status": "Updated",
                "id": 211,
                "lock_version": 5,
                "stale": None,
                "uri": "/repositories/2/digital_objects/211",
                "warnings": [],
            },
        )
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
