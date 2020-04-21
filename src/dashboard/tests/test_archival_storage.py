# -*- coding: utf-8 -*-

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
from __future__ import absolute_import, unicode_literals

import json
import os

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, StreamingHttpResponse
from django.test import TestCase
from django.test.client import Client
import pytest

from components.archival_storage import atom, views
from components import helpers

import metsrw


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DISPOSITION = "Content-Disposition"
CONTENT_TYPE = "Content-Type"


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
def username():
    return "test"


@pytest.fixture
def password():
    return "test"


@pytest.fixture
def mets_hdr():
    return """<?xml version='1.0' encoding='UTF-8'?>
    <mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version1121/mets.xsd">
        <mets:metsHdr CREATEDATE="2020-01-20T15:22:15"/>
    </mets:mets>
    """


def dashboard_login_and_setup(client, django_user_model, username, password):
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    helpers.set_setting("dashboard_uuid", "test-uuid")


def get_streaming_response(streaming_content):
    response_text = ""
    for response_char in streaming_content:
        response_text = "{}{}".format(response_text, response_char)
    return response_text


def test_get_mets_unknown_mets(client, mocker, django_user_model, username, password):
    dashboard_login_and_setup(client, django_user_model, username, password)
    mocker.patch("elasticSearchFunctions.get_client")
    mocker.patch("elasticSearchFunctions.get_aip_data", side_effect=IndexError())
    response = client.get(
        "/archival-storage/download/aip/11111111-1111-1111-1111-111111111111/mets_download/"
    )
    assert isinstance(response, HttpResponseNotFound)


def test_get_mets_known_mets(
    client, mocker, django_user_model, username, password, mets_hdr
):
    sip_uuid = "22222222-2222-2222-2222-222222222222"
    dashboard_login_and_setup(client, django_user_model, username, password)
    mocker.patch("elasticSearchFunctions.get_client")
    mocker.patch(
        "elasticSearchFunctions.get_aip_data",
        return_value={"_source": {"name": "transfer-{}".format(sip_uuid)}},
    )
    mock_response = StreamingHttpResponse(mets_hdr)
    mock_content_type = "application/xml"
    mock_content_disposition = "attachment; filename=METS.{}.xml;".format(sip_uuid)
    mock_response[CONTENT_TYPE] = mock_content_type
    mock_response[CONTENT_DISPOSITION] = mock_content_disposition
    mocker.patch(
        "components.helpers.stream_mets_from_storage_service",
        return_value=mock_response,
    )
    response = client.get(
        "/archival-storage/download/aip/{}/mets_download/".format(sip_uuid)
    )
    response_text = get_streaming_response(response.streaming_content)
    assert response_text == mets_hdr
    assert response.get(CONTENT_TYPE) == mock_content_type
    assert response.get(CONTENT_DISPOSITION) == mock_content_disposition


def test_get_pointer_unknown_pointer(
    client, mocker, django_user_model, username, password
):
    sip_uuid = "33333333-3333-3333-3333-333333333331"
    pointer_url = "http://archivematica-storage-service:8000/api/v2/file/{}/pointer_file".format(
        sip_uuid
    )
    dashboard_login_and_setup(client, django_user_model, username, password)
    mocker.patch("elasticSearchFunctions.get_client")
    mocker.patch("storageService.pointer_file_url", return_value=pointer_url)
    mock_status_code = 404
    mock_error_message = {"status": "False", "message": "an error status"}
    mock_response = helpers.json_response(mock_error_message, mock_status_code)
    mocker.patch(
        "components.helpers.stream_file_from_storage_service",
        return_value=mock_response,
    )
    response = client.get(
        "/archival-storage/download/aip/{}/pointer_file/".format(sip_uuid)
    )
    assert isinstance(response, HttpResponse)
    assert response.status_code == mock_status_code
    assert json.loads(response.content) == mock_error_message


def test_get_pointer_known_pointer(
    client, mocker, django_user_model, username, password, mets_hdr
):
    sip_uuid = "44444444-4444-4444-4444-444444444444"
    pointer_url = "http://archivematica-storage-service:8000/api/v2/file/{}/pointer_file".format(
        sip_uuid
    )
    pointer_file = "pointer.{}.xml".format(sip_uuid)
    content_disposition = 'attachment; filename="{}"'.format(pointer_file)
    dashboard_login_and_setup(client, django_user_model, username, password)
    mocker.patch("storageService.pointer_file_url", return_value=pointer_url)
    mock_content_type = "application/xml"
    mock_response = StreamingHttpResponse(mets_hdr)
    mock_response[CONTENT_TYPE] = mock_content_type
    mock_response[CONTENT_DISPOSITION] = content_disposition
    mocker.patch(
        "components.helpers.stream_file_from_storage_service",
        return_value=mock_response,
    )
    response = client.get(
        "/archival-storage/download/aip/{}/pointer_file/".format(sip_uuid)
    )
    response_text = get_streaming_response(response.streaming_content)
    assert response_text == mets_hdr
    assert response.get(CONTENT_TYPE) == mock_content_type
    assert response.get(CONTENT_DISPOSITION) == content_disposition


class TestArchivalStorageDataTableState(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")
        self.data = '{"time":1588609847900,"columns":[{"visible":true},{"visible":true},{"visible":false},{"visible":true},{"visible":false},{"visible":false},{"visible":true},{"visible":true},{"visible":false},{"visible":true}]}'

    def test_save_datatable_state(self):
        """Test ability to save DataTable state"""
        response = self.client.post(
            "/archival-storage/save_state/aips/",
            self.data,
            content_type="application/json",
        )
        assert response.status_code == 200
        saved_state = helpers.get_setting("aips_datatable_state")
        assert json.dumps(self.data) == saved_state

    def test_load_datatable_state(self):
        """Test ability to load DataTable state"""
        helpers.set_setting("aips_datatable_state", json.dumps(self.data))
        # Retrieve data from view
        response = self.client.get(reverse(views.load_state, args=["aips"]))
        assert response.status_code == 200
        payload = json.loads(response.content.decode("utf8"))
        assert payload["time"] == 1588609847900
        assert payload["columns"][0]["visible"] is True
        assert payload["columns"][2]["visible"] is False

    def test_load_datatable_state_404(self):
        """Non-existent settings should return a 404"""
        response = self.client.get(reverse(views.load_state, args=["nonexistent"]))
        assert response.status_code == 404
        payload = json.loads(response.content.decode("utf8"))
        assert payload["error"] is True
        assert payload["message"] == "Setting not found"
