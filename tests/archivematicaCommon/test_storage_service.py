"""Test Storage Service

Tests for the Archivematica Common Storage Service helpers.
"""

import json
import uuid
from unittest import mock

import pytest
from requests import Response

from archivematica.archivematicaCommon.storageService import (
    location_description_from_slug,
)
from archivematica.archivematicaCommon.storageService import request_file_deletion
from archivematica.archivematicaCommon.storageService import (
    retrieve_storage_location_description,
)


def mock_response(status_code, content_type, content):
    response = Response()
    response.status_code = status_code
    response.headers["content-type"] = content_type
    response.status = "Mocked status value"
    response._content = json.dumps(content).encode("utf8")
    return response


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status_code,content_type,expected_result",
    [
        (200, "application/json", {"description": "a description", "path": "/a/path/"}),
        (200, "application/gzip", {}),
        (204, "x-application/mocked", {}),
        (400, "x-application/mocked", {}),
        (500, "x-application/mocked", {}),
        (0, "", {}),
    ],
)
@mock.patch("archivematica.archivematicaCommon.storageService._storage_service_url")
@mock.patch("requests.Session.get")
def test_location_desc_from_slug(
    get, _storage_service_url, status_code, content_type, expected_result
):
    """Test location description from slug

    Rudimentary test to ensure that we're returning something that
    implements .get() for any potential return from this function. And
    that we get something sensible for unexpected status codes.
    """

    get.return_value = mock_response(status_code, content_type, expected_result)
    res = location_description_from_slug("mock_uri")
    assert res == expected_result, f"Unexpected result for status test: {status_code}"


@pytest.mark.parametrize(
    "slug,return_value,expected_result",
    [
        (
            f"/api/v2/location/{uuid.uuid4()}/",
            {"description": "a description"},
            "a description",
        ),
        (
            "/api/v2/location/default/AS/",
            {"description": None, "path": "/path/one/"},
            "/path/one/",
        ),
        (
            f"/api/v2/location/{uuid.uuid4()}/",
            {"path": "/path/two"},
            "/path/two",
        ),
        (
            f"/api/v2/location/{uuid.uuid4()}/",
            {"description": "a description", "path": "/path/three"},
            "a description",
        ),
        (f"/api/v2/location/{uuid.uuid4()}/", {}, ""),
    ],
    ids=[
        "description",
        "default_location_path",
        "path",
        "description_and_path",
        "empty",
    ],
)
@mock.patch(
    "archivematica.archivematicaCommon.storageService.location_description_from_slug"
)
def test_retrieve_storage_location(
    location_description_from_slug, slug, return_value, expected_result
):
    """Test retrieve storage location

    Ensure that we're able to retrieve the resource description for the
    storage service from our request to the storage service. We should
    be able to retrieve a 'description' or "path" or "" (blank string)
    in that order, depending on the response, i.e. if a user hasn't
    specified a description, we should be able to fall-back on something
    else. Likewise if we receive something unexpected.
    """
    location_description_from_slug.return_value = return_value
    res = retrieve_storage_location_description(slug)
    assert res == expected_result


@pytest.mark.django_db
@mock.patch("archivematica.archivematicaCommon.storageService._storage_api_session")
@mock.patch(
    "archivematica.archivematicaCommon.storageService._storage_service_url",
    return_value="http://ss/",
)
def test_request_file_deletion_handles_non_json_response(
    _storage_service_url, _storage_api_session
):
    response = Response()
    response.status_code = 404
    response.headers["content-type"] = "text/plain"
    response._content = b"Not Found"
    session = mock.Mock()
    session.post.return_value = response
    _storage_api_session.return_value = session

    result = request_file_deletion(
        str(uuid.uuid4()),
        0,
        "archivematica@example.com",
        "testing",
    )

    assert result == {"error": True, "message": "Not Found", "status": 404}
