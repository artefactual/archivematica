#!/usr/bin/env python
import os

from django.test import TestCase
from requests_mock import Mocker

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
import dip_generation_helper

from main.models import ArchivesSpaceDIPObjectResourcePairing


class TestParseArchivesSpaceIDs(TestCase):
    fixture_files = ["sip.json", "files.json", "archivesspaceconfig.json"]
    sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def test_no_archivesspace_csv(self):
        """It should do nothing."""
        sip_path = os.path.join(THIS_DIR, "fixtures", "emptysip", "")
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
        rc = dip_generation_helper.parse_archivesspace_ids(sip_path, self.sip_uuid)
        assert rc == 0
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False

    def test_empty_csv(self):
        """It should do nothing if the CSV is empty."""
        sip_path = os.path.join(THIS_DIR, "fixtures", "empty_metadata_files", "")
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
        rc = dip_generation_helper.parse_archivesspace_ids(sip_path, self.sip_uuid)
        assert rc == 1
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False

    @Mocker()
    def test_no_files_in_db(self, requests_mock):
        """It should do nothing if no files are found in the DB."""
        requests_mock.post(
            "http://localhost:8089/users/admin/login",
            json={
                "session": "88373637ab6bd52646d959ad310c1f281fb4ba02073e64c3f4da50b43d67b24a",
                "user": {
                    "lock_version": 1159,
                    "username": "admin",
                    "name": "Administrator",
                    "is_system_user": True,
                    "create_time": "2014-12-05T20:32:17Z",
                    "system_mtime": "2015-07-09T23:18:47Z",
                    "user_mtime": "2015-07-09T23:18:47Z",
                    "jsonmodel_type": "user",
                    "groups": [],
                    "is_admin": False,
                    "uri": "/users/1",
                    "agent_record": {"ref": "/agents/people/1"},
                    "permissions": {
                        "/repositories/2": [
                            "view_repository",
                            "update_accession_record",
                            "update_resource_record",
                            "update_digital_object_record",
                        ],
                        "_archivesspace": [],
                    },
                },
            },
        )
        sip_path = os.path.join(THIS_DIR, "fixtures", "metadata_csv_sip", "")
        sip_uuid = "dne"
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
        rc = dip_generation_helper.parse_archivesspace_ids(sip_path, sip_uuid)
        assert rc == 0
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False

    @Mocker()
    def test_parse_to_db(self, requests_mock):
        """
        It should create an entry in ArchivesSpaceDIPObjectResourcePairing for each file in archivesspaceids.csv
        It should match the reference ID to a resource ID.
        """
        requests_mock.post(
            "http://localhost:8089/users/admin/login",
            json={
                "session": "4a108561f24f7850cb136cd765405fd563853b39b626e7cf3bfc4a99ef2bab0c",
                "user": {
                    "lock_version": 898,
                    "username": "admin",
                    "name": "Administrator",
                    "is_system_user": True,
                    "create_time": "2014-12-05T20:32:17Z",
                    "system_mtime": "2015-07-08T21:38:45Z",
                    "user_mtime": "2015-07-08T21:38:45Z",
                    "jsonmodel_type": "user",
                    "groups": [],
                    "is_admin": False,
                    "uri": "/users/1",
                    "agent_record": {"ref": "/agents/people/1"},
                    "permissions": {
                        "/repositories/2": [
                            "view_repository",
                            "update_accession_record",
                            "update_resource_record",
                            "update_digital_object_record",
                        ],
                        "_archivesspace": [],
                    },
                },
            },
        )
        requests_mock.get(
            "http://localhost:8089/repositories/2/find_by_id/archival_objects?resolve%5B%5D=archival_objects&ref_id%5B%5D=a118514fab1b2ee6a7e9ad259e1de355",
            json={
                "archival_objects": [
                    {
                        "ref": "/repositories/2/archival_objects/752250",
                        "_resolved": {
                            "lock_version": 0,
                            "position": 0,
                            "publish": True,
                            "ref_id": "a118514fab1b2ee6a7e9ad259e1de355",
                            "component_id": "test111",
                            "title": "TestAO",
                            "display_string": "Test AO",
                            "restrictions_apply": False,
                            "created_by": "admin",
                            "last_modified_by": "admin",
                            "create_time": "2015-09-22T18:35:41Z",
                            "system_mtime": "2015-09-22T18:35:41Z",
                            "user_mtime": "2015-09-22T18:35:41Z",
                            "suppressed": False,
                            "level": "file",
                            "jsonmodel_type": "archival_object",
                            "external_ids": [],
                            "subjects": [],
                            "linked_events": [],
                            "extents": [],
                            "dates": [],
                            "external_documents": [],
                            "rights_statements": [],
                            "linked_agents": [],
                            "instances": [],
                            "notes": [],
                            "uri": "/repositories/2/archival_objects/752250",
                            "repository": {"ref": "/repositories/2"},
                            "resource": {"ref": "/repositories/2/resources/11319"},
                            "has_unpublished_ancestor": False,
                        },
                    }
                ]
            },
        )
        sip_path = os.path.join(THIS_DIR, "fixtures", "archivesspaceid_sip", "")
        assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
        rc = dip_generation_helper.parse_archivesspace_ids(sip_path, self.sip_uuid)
        assert rc == 0
        assert len(ArchivesSpaceDIPObjectResourcePairing.objects.all()) == 1
        r = ArchivesSpaceDIPObjectResourcePairing.objects.all()[0]
        assert str(r.dipuuid) == self.sip_uuid
        assert str(r.fileuuid) == "ae8d4290-fe52-4954-b72a-0f591bee2e2f"
        assert r.resourceid == "/repositories/2/archival_objects/752250"
