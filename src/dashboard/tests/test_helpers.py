# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import requests

import pytest

from amclient import AMClient
from components import helpers

CONTENT_TYPE = "content-type"
CONTENT_DISPOSITION = "content-disposition"

CONTENT_JSON = "application/json"
CONTENT_TEXT = "text/plain"
CONTENT_XML = "application/xml"

RESPONSE_200 = 200
RESPONSE_400 = 400
RESPONSE_404 = 404
RESPONSE_500 = 500
RESPONSE_503 = 503

SUCCESS = "success"
MESSAGE = "message"


@pytest.fixture
def mets_hdr():
    return """<?xml version='1.0' encoding='UTF-8'?>
    <mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version1121/mets.xsd">
        <mets:metsHdr CREATEDATE="2020-01-21T15:43:07"/>
    </mets:mets>
    """


def setup_ptr_info(sip_uuid):
    pointer_url = (
        "http://archivematica-storage-service:8000/api/v2/file/{}/pointer_file".format(
            sip_uuid
        )
    )
    pointer_file = "pointer.{}.xml".format(sip_uuid)
    content_disposition = 'attachment; filename="{}"'.format(pointer_file)
    return pointer_url, pointer_file, content_disposition


def get_streaming_response(streaming_content):
    response_text = ""
    for response_char in streaming_content:
        response_text = "{}{}".format(response_text, response_char.decode("utf8"))
    return response_text


"""
def mock_amclient_details(mocker, side_effect=None):
    mocker.patch(
        "components.helpers.get_setting", return_value="http://storage-service-url/"
    )
    amclient_mock = mocker.Mock(**{"extract_file.side_effect": side_effect})
    mocker.patch("components.helpers.AMClient", return_value=amclient_mock)
"""


def mock_amclient_details(mocker, return_value=None, side_effect=None):
    mocker.patch(
        "components.helpers.get_setting", return_value="http://storage-service-url/"
    )
    if side_effect:
        mocker.patch.object(AMClient, "extract_file", side_effect=side_effect)
    # A requests.Response() object can evaluate to None, e.g. where response.status_code = 500
    elif return_value is not None:
        mocker.patch.object(AMClient, "extract_file", return_value=return_value)


def mets_stream(tmpdir, mets_hdr):
    mets_stream = tmpdir.join("mets_file")
    mets_stream.write(mets_hdr)
    return mets_stream.open()


def test_stream_mets_from_disconnected_storage(mocker):
    custom_error_message = "Error connecting to the storage service"
    mock_amclient_details(
        mocker, side_effect=requests.exceptions.ConnectionError(custom_error_message)
    )
    response = helpers.stream_mets_from_storage_service(
        transfer_name="mets_transfer", sip_uuid="11111111-1111-1111-1111-111111111111"
    )
    assert response[CONTENT_TYPE] == CONTENT_JSON
    err = json.loads(response.content)
    assert err.get(SUCCESS) is False
    assert custom_error_message in err.get(MESSAGE)
    assert response.status_code == RESPONSE_503


def test_stream_mets_from_storage_no_file(mocker, tmp_path):
    custom_error_message = "Rsync failed with status 23: sending incremental file list"
    mock_response = requests.Response()
    mock_response._content = custom_error_message
    mock_response.status_code = 500
    mock_amclient_details(mocker, return_value=mock_response)
    response = helpers.stream_mets_from_storage_service(
        transfer_name="mets_transfer", sip_uuid="22222222-2222-2222-2222-222222222222"
    )
    assert response[CONTENT_TYPE] == CONTENT_JSON
    err = json.loads(response.content)
    assert err.get(SUCCESS) is False
    assert custom_error_message in err.get(MESSAGE)
    assert response.status_code == RESPONSE_500


def test_stream_mets_from_storage_success(mocker, mets_hdr, tmpdir):
    sip_uuid = "33333333-3333-3333-3333-333333333333"
    mets_file = "METS.{}.xml".format(sip_uuid)
    mock_response = requests.Response()
    mock_response.headers = {
        CONTENT_DISPOSITION: "attachment; filename={};".format(mets_file)
    }
    mock_response.status_code = RESPONSE_200
    mock_response.raw = mets_stream(tmpdir, mets_hdr)
    mock_amclient_details(mocker, return_value=mock_response)
    response = helpers.stream_mets_from_storage_service(
        transfer_name="mets_transfer", sip_uuid=sip_uuid
    )
    assert response.get(CONTENT_TYPE) == CONTENT_XML
    assert response.get(CONTENT_DISPOSITION) == "attachment; filename={};".format(
        mets_file
    )
    response_text = get_streaming_response(response.streaming_content)
    assert response_text == mets_hdr


def test_stream_pointer_from_storage_unsuccessful(mocker):
    pointer_url = "http://archivematica-storage-service:8000/api/v2/file/44444444-4444-4444-4444-444444444444/pointer_file"
    custom_error_message = "Unable to retrieve AIP pointer file from Storage Service"
    mock_response = requests.Response()
    mock_response.status_code = RESPONSE_503
    mocker.patch("requests.get", return_value=mock_response)
    response = helpers.stream_file_from_storage_service(
        pointer_url, error_message=custom_error_message
    )
    assert response[CONTENT_TYPE] == CONTENT_JSON
    err = json.loads(response.content)
    assert err.get(SUCCESS) is False
    assert custom_error_message in err.get(MESSAGE)
    assert response.status_code == RESPONSE_400


def test_stream_pointer_from_storage_successful(mocker, tmpdir, mets_hdr):
    sip_uuid = "55555555-5555-5555-5555-555555555555"
    mock_response = requests.Response()
    pointer_url, pointer_file, content_disposition = setup_ptr_info(sip_uuid)
    mock_response.headers = {
        CONTENT_TYPE: CONTENT_XML,
        CONTENT_DISPOSITION: content_disposition,
    }
    mock_response.status_code = RESPONSE_200
    mock_response.raw = mets_stream(tmpdir, mets_hdr)
    mocker.patch("requests.get", return_value=mock_response)
    response = helpers.stream_file_from_storage_service(pointer_url)
    assert response.status_code == RESPONSE_200
    assert response.get(CONTENT_TYPE) == CONTENT_XML
    assert response.get(CONTENT_DISPOSITION) == content_disposition
    response_text = get_streaming_response(response.streaming_content)
    assert response_text == mets_hdr
    # Create a new mock response object (the stream hasn't been consumed).
    mock_response = requests.Response()
    mock_response.status_code = RESPONSE_200
    mock_response.raw = mets_stream(tmpdir, mets_hdr)
    mocker.patch("requests.get", return_value=mock_response)
    # Make the request again, but ask to view in the browser, i.e. inline.
    response = helpers.stream_file_from_storage_service(pointer_url, preview_file=True)
    assert response.get(CONTENT_DISPOSITION) == "inline"
    response_text = get_streaming_response(response.streaming_content)
    assert response_text == mets_hdr


def test_stream_pointer_from_storage_no_content_type(mocker, tmpdir, mets_hdr):
    sip_uuid = "66666666-6666-6666-6666-666666666666"
    mock_response = requests.Response()
    pointer_url, pointer_file, content_disposition = setup_ptr_info(sip_uuid)
    mock_response.headers = {CONTENT_DISPOSITION: content_disposition}
    mock_response.status_code = RESPONSE_200
    mock_response.raw = mets_stream(tmpdir, mets_hdr)
    mocker.patch.object(requests, "get", return_value=mock_response)
    response = helpers.stream_file_from_storage_service(pointer_url)
    assert response.status_code == RESPONSE_200
    # The content type will be set to text/plain according to the function.
    assert response.get(CONTENT_TYPE) == CONTENT_TEXT
    # Other parts of the response should remain the same.
    assert response.get(CONTENT_DISPOSITION) == content_disposition
    response_text = get_streaming_response(response.streaming_content)
    assert response_text == mets_hdr
