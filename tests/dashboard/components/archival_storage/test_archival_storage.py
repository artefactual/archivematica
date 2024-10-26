# This file is part of Archivematica.
#
# Copyright 2010-2019 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
import json
import os
import pathlib
import uuid
from io import StringIO
from unittest import mock
from urllib.parse import urlencode

import metsrw
import pytest
from agentarchives.atom.client import CommunicationError
from components import helpers
from components.archival_storage import atom
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import StreamingHttpResponse
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from elasticsearch import Elasticsearch
from main.models import DashboardSetting

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DISPOSITION = "Content-Disposition"
CONTENT_TYPE = "Content-Type"
JSON_MIME = "application/json"

TEST_USER_FIXTURE = (
    pathlib.Path(__file__).parent.parent.parent / "fixtures" / "test_user.json"
)


@pytest.fixture
def amsetup(db):
    setting, _ = DashboardSetting.objects.get_or_create(
        name="dashboard_uuid", defaults={"value": str(uuid.uuid4())}
    )
    return {
        "uuid": setting.value,
    }


@pytest.fixture
def mets_document():
    return metsrw.METSDocument.fromfile(
        os.path.join(THIS_DIR, "fixtures", "mets_two_files.xml")
    )


def test_load_premis(mets_document):
    """Test the load of PREMIS 2 or PREMIS 3 from a given METS document."""

    # Load from PREMIS2
    data = {"foo": "bar"}
    atom._load_premis(
        data, mets_document.get_file(file_uuid="ae8d4290-fe52-4954-b72a-0f591bee2e2f")
    )
    assert data == {
        "foo": "bar",
        "format_name": "JPEG 1.02",
        "format_version": "1.02",
        "format_registry_key": "fmt/44",
        "format_registry_name": "PRONOM",
        "size": "158131",
    }

    # Load from PREMIS3
    data = {"foo": "bar"}
    atom._load_premis(
        data, mets_document.get_file(file_uuid="4583c44a-046c-4324-9584-345e8b8d82dd")
    )
    assert data == {
        "foo": "bar",
        "format_name": "Format name",
        "format_version": "Format version",
        "format_registry_key": "fmt/12345",
        "format_registry_name": "PRONOM",
        "size": "999999",
    }


@pytest.fixture
def mets_hdr():
    return """<?xml version='1.0' encoding='UTF-8'?>
    <mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version1121/mets.xsd">
        <mets:metsHdr CREATEDATE="2020-01-20T15:22:15"/>
    </mets:mets>
    """


def get_streaming_response(streaming_content):
    response_text = ""
    for response_char in streaming_content:
        response_text = "{}{}".format(response_text, response_char.decode("utf8"))
    return response_text


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.get_aip_data", side_effect=IndexError())
def test_get_mets_unknown_mets(get_aip_data, get_client, amsetup, admin_client):
    response = admin_client.get(
        "/archival-storage/download/aip/11111111-1111-1111-1111-111111111111/mets_download/"
    )
    assert isinstance(response, HttpResponseNotFound)


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.get_aip_data")
@mock.patch("components.helpers.stream_mets_from_storage_service")
def test_get_mets_known_mets(
    stream_mets_from_storage_service,
    get_aip_data,
    get_client,
    amsetup,
    admin_client,
    mets_hdr,
):
    sip_uuid = "22222222-2222-2222-2222-222222222222"
    get_aip_data.return_value = {"_source": {"name": f"transfer-{sip_uuid}"}}
    mock_response = StreamingHttpResponse(mets_hdr)
    mock_content_type = "application/xml"
    mock_content_disposition = f"attachment; filename=METS.{sip_uuid}.xml;"
    mock_response[CONTENT_TYPE] = mock_content_type
    mock_response[CONTENT_DISPOSITION] = mock_content_disposition
    stream_mets_from_storage_service.return_value = mock_response
    response = admin_client.get(
        f"/archival-storage/download/aip/{sip_uuid}/mets_download/"
    )
    response_text = get_streaming_response(response.streaming_content)
    assert response_text == mets_hdr
    assert response.get(CONTENT_TYPE) == mock_content_type
    assert response.get(CONTENT_DISPOSITION) == mock_content_disposition


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("storageService.pointer_file_url")
@mock.patch("components.helpers.stream_file_from_storage_service")
def test_get_pointer_unknown_pointer(
    stream_file_from_storage_service,
    pointer_file_url,
    get_client,
    amsetup,
    admin_client,
):
    sip_uuid = "33333333-3333-3333-3333-333333333331"
    pointer_url = (
        f"http://archivematica-storage-service:8000/api/v2/file/{sip_uuid}/pointer_file"
    )
    pointer_file_url.return_value = pointer_url
    mock_status_code = 404
    mock_error_message = {"status": "False", "message": "an error status"}
    mock_response = helpers.json_response(mock_error_message, mock_status_code)
    stream_file_from_storage_service.return_value = mock_response
    response = admin_client.get(
        f"/archival-storage/download/aip/{sip_uuid}/pointer_file/"
    )
    assert isinstance(response, HttpResponse)
    assert response.status_code == mock_status_code
    assert json.loads(response.content) == mock_error_message


@mock.patch("storageService.pointer_file_url")
@mock.patch("components.helpers.stream_file_from_storage_service")
def test_get_pointer_known_pointer(
    stream_file_from_storage_service, pointer_file_url, amsetup, admin_client, mets_hdr
):
    sip_uuid = "44444444-4444-4444-4444-444444444444"
    pointer_url = (
        f"http://archivematica-storage-service:8000/api/v2/file/{sip_uuid}/pointer_file"
    )
    pointer_file = f"pointer.{sip_uuid}.xml"
    content_disposition = f'attachment; filename="{pointer_file}"'
    pointer_file_url.return_value = pointer_url
    mock_content_type = "application/xml"
    mock_response = StreamingHttpResponse(mets_hdr)
    mock_response[CONTENT_TYPE] = mock_content_type
    mock_response[CONTENT_DISPOSITION] = content_disposition
    stream_file_from_storage_service.return_value = mock_response
    response = admin_client.get(
        f"/archival-storage/download/aip/{sip_uuid}/pointer_file/"
    )
    response_text = get_streaming_response(response.streaming_content)
    assert response_text == mets_hdr
    assert response.get(CONTENT_TYPE) == mock_content_type
    assert response.get(CONTENT_DISPOSITION) == content_disposition


def test_search_rejects_unsupported_file_mime(amsetup, admin_client):
    params = {"requestFile": "true", "file_mime": "application/json"}
    response = admin_client.get(
        "{}?{}".format(
            reverse("archival_storage:archival_storage_search"),
            urlencode(params),
        )
    )

    assert response.status_code == 400
    assert response.content == b"Please use ?mimeType=text/csv"


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticsearch.Elasticsearch.search")
@mock.patch(
    "components.archival_storage.views.search_augment_aip_results",
    return_value=[
        {
            "status": "Stored",
            "encrypted": False,
            "AICID": "AIC#2040",
            "countAIPsinAIC": 2,
            "accessionids": [],
            "uuid": "a341dbc0-9715-4806-8477-fb407b105a5e",
            "name": "tz",
            "created": 1594938100,
            "file_count": 2,
            "location": "/var/archivematica/AIPStore",
            "isPartOf": None,
            "bytes": 200100,
            "size": "200.1\xa0KB",
            "type": "AIC",
        },
        {
            "status": "Stored",
            "encrypted": True,
            "AICID": None,
            "countAIPsinAIC": None,
            "accessionids": ["Àà", "Éé", "Îî", "Ôô", "Ùù"],
            "uuid": "22423d5c-f992-4979-9390-1cb61c87da14",
            "name": "tz",
            "created": 1594938200,
            "file_count": 2,
            "location": "thé cloud",
            "isPartOf": None,
            "bytes": 152100,
            "size": "152.1\xa0KB",
            "type": "AIP",
        },
    ],
)
def test_search_as_csv(
    search_augment_aip_results, search, get_client, amsetup, admin_client, tmp_path
):
    """Test search as CSV

    Test the new route via the Archival Storage tab to be able to
    download the Elasticsearch AIP index as a CSV. Here we make sure
    that various headers are set as well as testing whether or not the
    data is returned correctly.
    """
    REQUEST_PARAMS = {
        "requestFile": True,
        "mimeType": "text/csv",
        "fileName": "test-filename.csv",
        "returnAll": True,
    }
    response = admin_client.get(
        "{}?{}".format(
            reverse("archival_storage:archival_storage_search"),
            urlencode(REQUEST_PARAMS),
        )
    )

    # Check that our response headers are going to be useful to the caller.
    assert response.get(CONTENT_TYPE) == "text/csv; charset=utf-8"
    assert (
        response.get(CONTENT_DISPOSITION) == 'attachment; filename="test-filename.csv"'
    )

    streamed_content = b"".join(list(response.streaming_content))
    csv_file = StringIO(streamed_content.decode("utf8"))

    assert csv_file.read() == (
        '"Name","UUID","AICID","Count AIPs in AIC","Bytes","Size","File count","Accession IDs","Created date (UTC)","Status","Type","Encrypted","Location"\n'
        '"tz","a341dbc0-9715-4806-8477-fb407b105a5e","AIC#2040","2","200100","200.1 KB","2","","2020-07-16 22:21:40+00:00","Stored","AIC","False","/var/archivematica/AIPStore"\n'
        '"tz","22423d5c-f992-4979-9390-1cb61c87da14","","","152100","152.1 KB","2","Àà; Éé; Îî; Ôô; Ùù","2020-07-16 22:23:20+00:00","Stored","AIP","True","thé cloud"\n'
    )


@mock.patch("elasticSearchFunctions.get_client", return_value=Elasticsearch())
@mock.patch("elasticSearchFunctions.Elasticsearch.search")
@mock.patch("components.archival_storage.views.search_augment_aip_results")
def test_search_as_csv_invalid_route(
    search_augment_aip_results,
    search,
    get_client,
    amsetup,
    admin_client,
    tmp_path,
):
    """Test search as CSV invalid rute

    Given the ability to download the Elasticsearch AIP index table as a
    CSV, make sure that the new pathway through the code does not
    impact the regular Archival Search component by performing a
    rudimentary test to just ensure that we can successfully NOT
    download the results as a CSV.
    """
    MOCK_TOTAL = 10
    AUG_RESULTS = {"mock": "response"}
    search.return_value = {
        "hits": {"total": MOCK_TOTAL},
        "aggregations": {
            "aip_uuids": {"buckets": [{"key": "mocked", "doc_count": "mocked"}]}
        },
    }
    search_augment_aip_results.return_value = [AUG_RESULTS]
    REQUEST_PARAMS = {"requestFile": False}
    response = admin_client.get(
        "{}?{}".format(
            reverse("archival_storage:archival_storage_search"),
            urlencode(REQUEST_PARAMS),
        )
    )
    expected_result = {
        "iTotalRecords": MOCK_TOTAL,
        "iTotalDisplayRecords": MOCK_TOTAL,
        "sEcho": 0,
        "aaData": [AUG_RESULTS],
    }
    assert response[CONTENT_TYPE] == JSON_MIME
    assert json.loads(response.content) == expected_result


class TestArchivalStorageDataTableState(TestCase):
    fixtures = [TEST_USER_FIXTURE]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")
        self.data = '{"time":1588609847900,"columns":[{"visible":true},{"visible":true},{"visible":false},{"visible":true},{"visible":false},{"visible":false},{"visible":true},{"visible":true},{"visible":false},{"visible":true}]}'

    def test_save_datatable_state(self):
        """Test ability to save DataTable state"""
        response = self.client.post(
            "/archival-storage/save_state/aips/", self.data, content_type=JSON_MIME
        )
        assert response.status_code == 200
        saved_state = helpers.get_setting("aips_datatable_state")
        assert json.dumps(self.data) == saved_state

    def test_load_datatable_state(self):
        """Test ability to load DataTable state"""
        helpers.set_setting("aips_datatable_state", json.dumps(self.data))
        # Retrieve data from view
        response = self.client.get(
            reverse("archival_storage:load_state", args=["aips"])
        )
        assert response.status_code == 200
        payload = json.loads(response.content.decode("utf8"))
        assert payload["time"] == 1588609847900
        assert payload["columns"][0]["visible"] is True
        assert payload["columns"][2]["visible"] is False

    def test_load_datatable_state_404(self):
        """Non-existent settings should return a 404"""
        response = self.client.get(
            reverse("archival_storage:load_state", args=["nonexistent"])
        )
        assert response.status_code == 404
        payload = json.loads(response.content.decode("utf8"))
        assert payload["error"] is True
        assert payload["message"] == "Setting not found"


@mock.patch("components.helpers.processing_config_path")
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.get_aip_data")
@mock.patch("components.archival_storage.forms.get_atom_client")
def test_view_aip_metadata_only_dip_upload_with_missing_description_slug(
    get_atom_client,
    get_aip_data,
    get_client,
    processing_config_path,
    amsetup,
    admin_client,
    tmpdir,
    processing_configurations_dir,
):
    processing_config_path.return_value = str(processing_configurations_dir)
    sip_uuid = uuid.uuid4()
    file_path = tmpdir.mkdir("file")
    get_aip_data.return_value = {
        "_source": {
            "name": f"transfer-{sip_uuid}",
            "filePath": str(file_path),
        }
    }
    get_atom_client.return_value = mock.Mock(
        **{
            "find_parent_id_for_component.side_effect": CommunicationError(
                404, mock.Mock(url="http://example.com")
            )
        }
    )

    response = admin_client.post(
        reverse("archival_storage:view_aip", args=[sip_uuid]),
        {"submit-upload-form": "1", "upload-slug": "missing-slug"},
    )

    assert "Description with slug missing-slug not found!" in response.content.decode(
        "utf8"
    )


def test_create_aic_fails_if_query_is_not_passed(amsetup, admin_client):
    params = {}
    response = admin_client.get(
        "{}?{}".format(
            reverse("archival_storage:create_aic"),
            urlencode(params),
        ),
        follow=True,
    )

    assert "Unable to create AIC: No AIPs selected" in response.content.decode()


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("databaseFunctions.createSIP")
@mock.patch(
    "uuid.uuid4", return_value=uuid.UUID("1e23e6e2-02d7-4b2d-a648-caffa3b489f3")
)
def test_create_aic_creates_temporary_files(
    uuid4, creat_sip, get_client, admin_client, settings, tmp_path, amsetup
):
    aipfiles_search_results = {
        "aggregations": {
            "aip_uuids": {
                "buckets": [
                    {"key": "a79e23a1-fd5d-4e54-bc02-b88521f9f35b", "doc_count": 15},
                    {"key": "786e25a5-fa60-48ab-9ff7-baabc52a9591", "doc_count": 15},
                ]
            }
        }
    }
    aip_search_results = {
        "_shards": {"failed": 0, "skipped": 0, "successful": 5, "total": 5},
        "hits": {
            "hits": [
                {
                    "_id": "LkAKUIkB6j_bcPXdWtl-",
                    "_index": "aips",
                    "_score": None,
                    "_source": {
                        "AICID": None,
                        "accessionids": [],
                        "countAIPsinAIC": None,
                        "created": 1689264994,
                        "encrypted": False,
                        "isPartOf": None,
                        "location": "Store AIP in standard " "Archivematica Directory",
                        "name": "artefactual",
                        "size": 4.80488395690918,
                        "status": "UPLOADED",
                        "uuid": "a79e23a1-fd5d-4e54-bc02-b88521f9f35b",
                    },
                    "_type": "_doc",
                    "sort": ["artefactual"],
                },
                {
                    "_id": "HEAIUIkB6j_bcPXdedka",
                    "_index": "aips",
                    "_score": None,
                    "_source": {
                        "AICID": None,
                        "accessionids": [],
                        "countAIPsinAIC": None,
                        "created": 1689264872,
                        "encrypted": False,
                        "isPartOf": None,
                        "location": "Store AIP in standard " "Archivematica Directory",
                        "name": "bunny_1",
                        "size": 4.805169105529785,
                        "status": "UPLOADED",
                        "uuid": "786e25a5-fa60-48ab-9ff7-baabc52a9591",
                    },
                    "_type": "_doc",
                    "sort": ["bunny_1"],
                },
            ],
            "max_score": None,
            "total": 2,
        },
        "timed_out": False,
        "took": 4,
    }
    get_client.return_value = mock.Mock(
        **{"search.side_effect": [aipfiles_search_results, aip_search_results]}
    )
    d = tmp_path / "test-aic"
    d.mkdir()
    (d / "tmp").mkdir()
    settings.SHARED_DIRECTORY = str(d)

    params = {"query": "", "field": "", "fieldName": "", "type": "term"}
    response = admin_client.get(
        "{}?{}".format(
            reverse("archival_storage:create_aic"),
            urlencode(params),
        ),
    )

    assert response.status_code == 302
    expected_file_contents = {
        ("a79e23a1-fd5d-4e54-bc02-b88521f9f35b", "artefactual"),
        ("786e25a5-fa60-48ab-9ff7-baabc52a9591", "bunny_1"),
    }
    temporary_files = set()
    for path in (d / "tmp" / "1e23e6e2-02d7-4b2d-a648-caffa3b489f3").iterdir():
        temporary_files.add((path.name, path.read_text().strip()))
    assert expected_file_contents == temporary_files


@pytest.fixture
def processing_configurations_dir(tmp_path):
    result = tmp_path / "sharedMicroServiceTasksConfigs" / "processingMCPConfigs"
    result.mkdir(parents=True)

    (result / "defaultProcessingMCP.xml").touch()
    (result / "automatedProcessingMCP.xml").touch()
    (result / "customProcessingMCP.xml").touch()

    return result


@mock.patch("components.helpers.processing_config_path")
@mock.patch(
    "elasticSearchFunctions.get_aip_data",
    return_value={"_source": {"name": "My AIP", "filePath": "path"}},
)
@mock.patch("elasticSearchFunctions.get_client")
def test_view_aip_reingest_form_displays_processing_configurations_choices(
    get_client,
    get_aip_data,
    processing_config_path,
    amsetup,
    admin_client,
    processing_configurations_dir,
):
    processing_config_path.return_value = str(processing_configurations_dir)
    response = admin_client.get(
        reverse("archival_storage:view_aip", args=[uuid.uuid4()])
    )
    assert response.status_code == 200

    content = response.content.decode().replace("\n", "")
    assert '<select name="reingest-processing_config"' in content
    assert (
        "  ".join(
            [
                '<option value="automated">automated</option>',
                '<option value="custom">custom</option>',
                '<option value="default" selected>default</option>',
            ]
        )
        in content
    )


@pytest.mark.parametrize(
    "error,message", [(False, "success!"), (True, "error!")], ids=["success", "error"]
)
@mock.patch("components.helpers.processing_config_path")
@mock.patch("storageService.request_reingest")
@mock.patch("elasticSearchFunctions.get_aip_data")
@mock.patch("elasticSearchFunctions.get_client")
def test_view_aip_reingest_form_submits_reingest(
    get_client,
    get_aip_data,
    request_reingest,
    processing_config_path,
    error,
    message,
    amsetup,
    admin_client,
    processing_configurations_dir,
):
    processing_config_path.return_value = str(processing_configurations_dir)
    request_reingest.return_value = {"error": error, "message": message}
    aip_uuid = str(uuid.uuid4())
    reingest_type = "metadata"
    processing_config = "default"

    response = admin_client.post(
        reverse("archival_storage:view_aip", args=[aip_uuid]),
        {
            "submit-reingest-form": "true",
            "reingest-reingest_type": reingest_type,
            "reingest-processing_config": processing_config,
        },
        follow=True,
    )
    assert response.status_code == 200

    request_reingest.assert_called_once_with(aip_uuid, reingest_type, processing_config)
    assert message in response.content.decode()
