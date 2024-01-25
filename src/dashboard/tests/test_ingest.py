import json
import os
import pickle
import uuid
from unittest import mock

import pytest
from agentarchives.archivesspace import ArchivesSpaceError
from archivematicaFunctions import b64decode_string
from components import helpers
from components.ingest.views import _adjust_directories_draggability
from components.ingest.views import _es_results_to_appraisal_tab_format
from components.ingest.views_as import get_as_system_client
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from main.models import Access
from main.models import ArchivesSpaceDIPObjectResourcePairing
from main.models import DashboardSetting


class TestIngest(TestCase):
    fixtures = ["test_user", "sip", "jobs-sip-complete"]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    @mock.patch("agentarchives.archivesspace.ArchivesSpaceClient._login")
    def test_get_as_system_client(self, __):
        DashboardSetting.objects.set_dict(
            "upload-archivesspace_v0.0",
            {
                "base_url": "http://foobar.tld",
                "user": "user",
                "passwd": "12345",
                "repository": "5",
            },
        )
        client = get_as_system_client()
        assert client.base_url == "http://foobar.tld"
        assert client.user == "user"
        assert client.passwd == "12345"
        assert client.repository == "/repositories/5"

        # It raises error when "base_url" is missing.
        DashboardSetting.objects.set_dict(
            "upload-archivesspace_v0.0",
            {"user": "user", "passwd": "12345", "repository": "5"},
        )
        with pytest.raises(ArchivesSpaceError):
            client = get_as_system_client()

        # It raises error when "base_url" is empty.
        DashboardSetting.objects.set_dict(
            "upload-archivesspace_v0.0",
            {"base_url": "", "user": "user", "passwd": "12345", "repository": "5"},
        )
        with pytest.raises(ArchivesSpaceError):
            client = get_as_system_client()

    def test_normalization_event_detail_view(self):
        """Test the 'Manual normalization event detail' view of a SIP"""
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        url = reverse("ingest:ingest_metadata_event_detail", args=[sip_uuid])
        response = self.client.get(url)
        assert response.status_code == 200
        title = "".join(
            ["<h1>" "Normalization Event Detail<br />", "<small>test</small>", "</h1>"]
        )
        assert title in response.content.decode("utf8")

    def test_add_metadata_files_view(self):
        """Test the 'Add metadata files' view of a SIP"""
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        url = reverse("ingest:ingest_metadata_add_files", args=[sip_uuid])
        response = self.client.get(url)
        assert response.status_code == 200
        title = "\n    ".join(
            ["<h1>", "  Add metadata files<br />", "  <small>test</small>", "</h1>"]
        )
        assert title in response.content.decode("utf8")

    def test_ingest_upload_get(self):
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        access_target = {"target": "description-slug"}
        Access.objects.create(
            sipuuid=sip_uuid,
            target=pickle.dumps(access_target, protocol=0).decode(),
        )

        response = self.client.get(
            reverse("ingest:ingest_upload", args=[sip_uuid]),
        )

        assert response.status_code == 200
        assert json.loads(response.content) == access_target

    def test_ingest_upload_post(self):
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        access_target = {"target": "description-slug"}

        # Check there is no Access object associated with the SIP yet.
        assert Access.objects.filter(sipuuid=sip_uuid).count() == 0

        response = self.client.post(
            reverse("ingest:ingest_upload", args=[sip_uuid]),
            data=access_target,
        )
        assert response.status_code == 200
        assert json.loads(response.content) == {"ready": True}

        # An Access object was created for the SIP with the right target.
        assert Access.objects.filter(sipuuid=sip_uuid).count() == 1
        access = Access.objects.get(sipuuid=sip_uuid)
        assert pickle.loads(access.target.encode()) == access_target


def _assert_file_node_properties_match_record(file_node, record):
    assert file_node["type"] == "file"
    assert file_node["id"] == record["fileuuid"]
    # the relative path of the node is encoded
    assert b64decode_string(file_node["relative_path"]) == record["relative_path"]
    # the node title is the encoded file name
    assert b64decode_string(file_node["title"]) == os.path.basename(
        record["relative_path"]
    )
    assert file_node["size"] == record["size"]
    assert file_node["tags"] == record["tags"]
    # files are draggable into arrangement by default
    assert not file_node["not_draggable"]


def test_appraisal_tab_node_formatter():
    """Test the _es_results_to_appraisal_tab_format helper that formats
    the ElasticSearch results to be used in the appraisal tab JS code.
    """
    record = {
        "relative_path": "transfer-directory/data/objects/MARBLES.TGA",
        "fileuuid": "ea7a98d4-dcb5-46b3-a9dd-82262bd983aa",
        "size": 4.0,
        "tags": ["tag1", "tag2"],
        "bulk_extractor_reports": [],
        "modification_date": None,
        "format": None,
    }
    mapping = {}
    # this parameter is modified in place and will contain
    # formatted nodes for each transfer
    nodes = []
    _es_results_to_appraisal_tab_format(record, mapping, nodes)
    # extract the only transfer node at the moment
    transfer_node = nodes[0]
    assert transfer_node["type"] == "transfer"
    # there are child nodes for each directory in the path
    data_dir_node = transfer_node["children"][0]
    assert data_dir_node["type"] == "directory"
    objects_dir_node = data_dir_node["children"][0]
    assert objects_dir_node["type"] == "directory"
    # and finally a node for the file
    file_node = objects_dir_node["children"][0]
    # check that the file node properties match the record properties
    _assert_file_node_properties_match_record(file_node, record)


def test_appraisal_tab_node_formatter_old_transfer_format():
    """
    Test the _es_results_to_appraisal_tab_format helper works with the
    pre bag transfer layout (no data directory).
    """
    record = {
        "relative_path": "transfer-directory/objects/MARBLES.TGA",
        "fileuuid": "ea7a98d4-dcb5-46b3-a9dd-82262bd983aa",
        "size": 4.0,
        "tags": ["tag1", "tag2"],
        "bulk_extractor_reports": [],
        "modification_date": None,
        "format": None,
    }
    mapping = {}
    # this parameter is modified in place and will contain
    # formatted nodes for each transfer
    nodes = []
    _es_results_to_appraisal_tab_format(record, mapping, nodes)
    # extract the only transfer node at the moment
    transfer_node = nodes[0]
    assert transfer_node["type"] == "transfer"
    # there are child nodes for each directory in the path
    objects_dir_node = transfer_node["children"][0]
    assert objects_dir_node["type"] == "directory"
    # and finally a node for the file
    file_node = objects_dir_node["children"][0]
    # check that the file node properties match the record properties
    _assert_file_node_properties_match_record(file_node, record)


def test_appraisal_tab_node_draggability_logs():
    """Test that the file nodes in the logs directory cannot be dragged"""
    record = {
        "relative_path": "transfer-directory/data/logs/arrange.log",
        "fileuuid": "c58db760-3767-4284-a3a3-40b9cad61095",
        "size": 1.0,
        "tags": [],
        "bulk_extractor_reports": [],
        "modification_date": None,
        "format": None,
    }
    mapping = {}
    nodes = []
    _es_results_to_appraisal_tab_format(record, mapping, nodes)
    transfer_node = nodes[0]
    data_dir_node = transfer_node["children"][0]
    # hidden directories can't be dragged either
    logs_dir_node = data_dir_node["children"][0]
    assert logs_dir_node["not_draggable"]
    file_node = logs_dir_node["children"][0]
    assert file_node["not_draggable"]


def test_appraisal_tab_node_draggability_metadata():
    """Test that the file nodes in the metadata directory cannot be dragged"""
    record = {
        "relative_path": "transfer-directory/data/metadata/directory_tree.txt",
        "fileuuid": "c58db760-3767-4284-a3a3-40b9cad61095",
        "size": 1.0,
        "tags": [],
        "bulk_extractor_reports": [],
        "modification_date": None,
        "format": None,
    }
    mapping = {}
    nodes = []
    _es_results_to_appraisal_tab_format(record, mapping, nodes)
    transfer_node = nodes[0]
    data_dir_node = transfer_node["children"][0]
    # hidden directories can't be dragged either
    metadata_dir_node = data_dir_node["children"][0]
    assert metadata_dir_node["not_draggable"]
    file_node = metadata_dir_node["children"][0]
    assert file_node["not_draggable"]


def test_appraisal_tab_node_draggability_bagit_manifest_files():
    """Test that the file nodes in the top level of the bag cannot be dragged"""
    record = {
        "relative_path": "transfer-directory/bag-info.txt",
        "fileuuid": "2bff65bc-46c8-4c38-87c3-c4bbba304c40",
        "size": 2.0,
        "tags": [],
        "bulk_extractor_reports": [],
        "modification_date": None,
        "format": None,
    }
    mapping = {}
    nodes = []
    _es_results_to_appraisal_tab_format(record, mapping, nodes)
    transfer_node = nodes[0]
    file_node = transfer_node["children"][0]
    assert file_node["not_draggable"]


def test_appraisal_tab_node_draggability_readme():
    """Test that the file node representing the transfer README cannot be dragged"""
    record = {
        "relative_path": "transfer-directory/data/README.html",
        "fileuuid": "bb318011-fb1f-4c41-8641-b35be5873b03",
        "size": 3.0,
        "tags": [],
        "bulk_extractor_reports": [],
        "modification_date": None,
        "format": None,
    }
    mapping = {}
    nodes = []
    _es_results_to_appraisal_tab_format(record, mapping, nodes)
    transfer_node = nodes[0]
    data_dir_node = transfer_node["children"][0]
    file_node = data_dir_node["children"][0]
    assert file_node["not_draggable"]


def test_appraisal_tab_node_draggability_explicit():
    """Test that a file node can be marked as not draggable explicitly"""
    record = {
        "relative_path": "transfer-directory/data/objects/picture.jpg",
        "fileuuid": "ea7a98d4-dcb5-46b3-a9dd-82262bd983aa",
        "size": 4.0,
        "tags": [],
        "bulk_extractor_reports": [],
        "modification_date": None,
        "format": None,
    }
    mapping = {}
    nodes = []
    _es_results_to_appraisal_tab_format(record, mapping, nodes, not_draggable=True)
    transfer_node = nodes[0]
    data_dir_node = transfer_node["children"][0]
    objects_dir_node = data_dir_node["children"][0]
    file_node = objects_dir_node["children"][0]
    assert file_node["not_draggable"]


def test_adjust_directories_draggability():
    """Test that directories in the appraisal tab can be dragged if they contain
    draggable descendants.
    """

    # Set up a tree with three directories
    cats = {
        "title": "cats",
        "not_draggable": False,
        "children": [
            {"relative_path": "mishy.txt", "not_draggable": False},
            {"relative_path": "pusheen.txt", "not_draggable": True},
        ],
    }
    dogs = {
        "title": "dogs",
        "not_draggable": False,
        "children": [{"relative_path": "roco.txt", "not_draggable": True}],
    }
    turtles = {
        "title": "turtles",
        "not_draggable": False,
        "children": [
            {
                "title": "large turtles",
                "not_draggable": False,
                "children": [{"relative_path": "esperanza.txt", "not_draggable": True}],
            },
            {
                "title": "small turtles",
                "not_draggable": False,
                "children": [
                    {"relative_path": "bututu.txt", "not_draggable": True},
                    {"relative_path": "cristal.txt", "not_draggable": False},
                ],
            },
        ],
    }

    # Adjust draggability of the directories in the tree
    _adjust_directories_draggability([cats, dogs, turtles])

    # cats has some draggable children so it's draggable
    assert not cats["not_draggable"]

    # dogs has no draggable children so it's not draggable
    assert dogs["not_draggable"]

    # turtles has some draggable grandchildren so it's draggable
    assert not turtles["not_draggable"]
    large_turtles = turtles["children"][0]
    small_turtles = turtles["children"][1]

    # large turtles has no draggable children so it's not draggable
    assert large_turtles["not_draggable"]

    # small turtles has some draggable children so it's draggable
    assert not small_turtles["not_draggable"]


@pytest.fixture
def dashboard_uuid(db):
    helpers.set_setting("dashboard_uuid", str(uuid.uuid4()))


@mock.patch("builtins.open")
@mock.patch("builtins.print")
def test_ingest_upload_as_match_shows_deleted_rows(
    print_mock, open_mock, admin_client, dashboard_uuid
):
    dip_uuid = uuid.uuid4()
    file_uuid = uuid.uuid4()
    ArchivesSpaceDIPObjectResourcePairing.objects.create(
        dipuuid=dip_uuid,
        fileuuid=file_uuid,
        resourceid="/repositories/2/archival_objects/1",
    )
    ArchivesSpaceDIPObjectResourcePairing.objects.create(
        dipuuid=dip_uuid,
        fileuuid=file_uuid,
        resourceid="/repositories/2/archival_objects/2",
    )

    response = admin_client.delete(
        reverse("ingest:ingest_upload_as_match", kwargs={"uuid": dip_uuid}),
        data=json.dumps(
            {
                "resource_id": "/repositories/2/archival_objects/1",
                "file_uuid": str(file_uuid),
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 204

    open_mock.assert_called_once_with("/tmp/delete.log", "a")
    print_mock.assert_called_once_with(
        "Resource",
        "/repositories/2/archival_objects/1",
        "File",
        "file_uuid",
        "matches",
        1,
        file=mock.ANY,
    )
