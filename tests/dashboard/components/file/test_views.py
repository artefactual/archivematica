import json
import logging
import uuid
from unittest import mock

import elasticSearchFunctions
import pytest
from components import helpers
from django.urls import reverse
from main import models


@pytest.fixture
def dashboard_uuid(db):
    helpers.set_setting("dashboard_uuid", str(uuid.uuid4()))


@pytest.fixture
def transfer(db):
    return models.Transfer.objects.create()


@pytest.fixture
def sip(db):
    return models.SIP.objects.create()


@pytest.fixture
def file(db):
    return models.File.objects.create()


@mock.patch("elasticSearchFunctions.get_client")
<<<<<<< HEAD
def test_file_details(_get_client, admin_client, dashboard_uuid, file, sip, mocker):
    mocker.patch(
        "elasticSearchFunctions.get_transfer_file_info",
        return_value={
            "filename": "LICENSE",
            "fileuuid": str(file.uuid),
            "sipuuid": str(sip.uuid),
            "status": "backlog",
            "size": 0.032919883728027344,
            "tags": [],
            "bulk_extractor_reports": [],
            "format": [
                {"puid": "x-fmt/111", "format": "Generic TXT", "group": "Text (Plain)"}
            ],
            "pending_deletion": False,
        },
    )
@mock.patch("elasticSearchFunctions.get_transfer_file_info")
def test_file_details(
    get_transfer_file_info, get_client, admin_client, dashboard_uuid, file, sip
):
    get_transfer_file_info.return_value = {
        "filename": "LICENSE",
        "fileuuid": str(file.uuid),
        "sipuuid": str(sip.uuid),
        "status": "backlog",
        "size": 0.032919883728027344,
        "tags": [],
        "bulk_extractor_reports": [],
        "format": [
            {"puid": "x-fmt/111", "format": "Generic TXT", "group": "Text (Plain)"}
        ],
        "pending_deletion": False,
    }

    response = admin_client.get(reverse("file:file_details", args=[file.uuid]))
    assert response.status_code == 200

    assert response.json() == {
        "id": str(file.uuid),
        "type": "file",
        "title": "LICENSE",
        "size": 0.032919883728027344,
        "bulk_extractor_reports": [],
        "tags": [],
        "format": "Generic TXT",
        "group": "Text (Plain)",
        "puid": "x-fmt/111",
    }


@pytest.mark.parametrize(
    "error_message, status_code",
    [
        ("get_transfer_file_info returned no exact results", 404),
        ("unknown error", 500),
    ],
    ids=["no exact results", "unknown error"],
)
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.get_transfer_file_info")
def test_file_details_handle_exceptions(
    get_transfer_file_info,
    get_client,
    error_message,
    status_code,
    admin_client,
    dashboard_uuid,
    file,
):
    get_transfer_file_info.side_effect = elasticSearchFunctions.ElasticsearchError(
        error_message
    )
    response = admin_client.get(reverse("file:file_details", args=[file.uuid]))
    assert response.status_code == status_code

    assert response.json() == {
        "success": False,
        "message": error_message,
    }


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch(
    "elasticSearchFunctions.get_transfer_file_info",
    return_value={
        "filename": "piiTestDataCreditCardNumbers.txt",
        "relative_path": "test-bulk-extract-a239e3e1-0391-46da-94d7-25a3e8509b45/data/objects/piiTestDataCreditCardNumbers.txt",
        "status": "backlog",
        "tags": [],
        "bulk_extractor_reports": ["ccn"],
        "format": [
            {"puid": "x-fmt/111", "format": "Generic TXT", "group": "Text (Plain)"}
        ],
    },
)
def test_bulk_extractor_fails_if_requested_file_is_missing(
    get_transfer_file_info, get_client, admin_client, dashboard_uuid, file, sip
):
    response = admin_client.get(reverse("file:bulk_extractor", args=[file.uuid]))
    assert response.status_code == 400

    assert response.json() == {
        "success": False,
        "message": "Requested file is missing the following requested reports: pii",
    }


@mock.patch("components.file.views.len", side_effect=[0])
def test_bulk_extractor_fails_if_no_reports_requested(
    _len, admin_client, dashboard_uuid, file
):
    response = admin_client.get(
        reverse("file:bulk_extractor", kwargs={"fileuuid": file.uuid})
    )
    assert response.status_code == 400

    assert response.json() == {
        "success": False,
        "message": "No reports were requested.",
    }


@pytest.mark.parametrize(
    "error_message, status_code",
    [
        ("get_transfer_file_info returned no exact results", 404),
        ("unknown error", 500),
    ],
    ids=["no exact results", "unknown error"],
)
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.get_transfer_file_info")
def test_bulk_extractor_handle_exceptions(
    get_transfer_file_info,
    get_client,
    error_message,
    status_code,
    admin_client,
    dashboard_uuid,
    file,
):
    get_transfer_file_info.side_effect = elasticSearchFunctions.ElasticsearchError(
        error_message
    )
    response = admin_client.get(
        reverse("file:bulk_extractor", kwargs={"fileuuid": file.uuid})
    )
    assert response.status_code == status_code

    assert response.json() == {
        "success": False,
        "message": error_message,
    }


@pytest.mark.django_db
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.get_transfer_file_info")
def test_bulk_extractor(
    get_transfer_file_info,
    get_client,
    admin_client,
    dashboard_uuid,
    transfer,
    sip,
    file,
):
    file.transfer = transfer
    file.sip = sip
    file.save()
    get_transfer_file_info.return_value = {
        "filename": "piiTestDataCreditCardNumbers.txt",
        "fileuuid": str(file.uuid),
        "sipuuid": str(sip.uuid),
        "status": "backlog",
        "tags": [],
        "bulk_extractor_reports": ["ccn", "pii"],
        "format": [
            {"puid": "x-fmt/111", "format": "Generic TXT", "group": "Text (Plain)"}
        ],
        "pending_deletion": False,
    }
    with mock.patch(
        "requests.get",
        return_value=mock.Mock(
            status_code=200,
            text="""64\t378282246310005	rican Express - 378282246310005 02. American E\t
 258\t3566002020360505\t9424 06. JCB - 3566002020360505 """,
        ),
    ):
        response = admin_client.get(
            reverse("file:bulk_extractor", kwargs={"fileuuid": file.uuid})
        )
    assert response.status_code == 200

    assert response.json() == {
        "ccn": [
            {
                "offset": "64",
                "content": "378282246310005",
                "context": "rican Express - 378282246310005 02. American E",
            },
            {
                "offset": " 258",
                "content": "3566002020360505",
                "context": "9424 06. JCB - 3566002020360505 ",
            },
        ],
        "pii": [
            {
                "offset": "64",
                "content": "378282246310005",
                "context": "rican Express - 378282246310005 02. American E",
            },
            {
                "offset": " 258",
                "content": "3566002020360505",
                "context": "9424 06. JCB - 3566002020360505 ",
            },
        ],
    }


@pytest.mark.django_db
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.get_transfer_file_info")
def test_bulk_extractor_handles_exception_if_no_missing_reports(
    get_transfer_file_info,
    get_client,
    admin_client,
    dashboard_uuid,
    caplog,
    transfer,
    sip,
    file,
):
    file.transfer = transfer
    file.sip = sip
    file.save()
    get_transfer_file_info.return_value = {
        "filename": "piiTestDataCreditCardNumbers.txt",
        "fileuuid": file.uuid,
        "sipuuid": sip.uuid,
        "status": "backlog",
        "tags": [],
        "bulk_extractor_reports": ["ccn", "pii"],
        "format": [
            {"puid": "x-fmt/111", "format": "Generic TXT", "group": "Text (Plain)"}
        ],
    }
    with mock.patch(
        "requests.get",
        return_value=mock.Mock(status_code=500, text="""Internal Server Error"""),
    ):
        response = admin_client.get(
            reverse("file:bulk_extractor", kwargs={"fileuuid": file.uuid})
        )
    assert response.status_code == 200

    assert (
        "archivematica.dashboard",
        40,
        f"Unable to retrieve ccn report for file with UUID {file.uuid}; response: ('Internal Server Error',)",
    ) in caplog.record_tuples
    assert [record.levelname == "ERROR" for record in caplog.records]
    assert caplog.at_level(logging.ERROR, logger="archivematica.dashboard")
    assert (
        f"Unable to retrieve ccn report for file with UUID {file.uuid};" in caplog.text
    )
    assert "response: ('Internal Server Error',)" in caplog.text


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch(
    "elasticSearchFunctions.get_file_tags",
    return_value=["test"],
)
def test_transfer_file_tags(
    get_file_tags, get_client, admin_client, dashboard_uuid, file
):
    response = admin_client.get(reverse("file:transfer_file_tags", args=[file.uuid]))
    assert response.status_code == 200

    assert response.json() == ["test"]


@pytest.mark.parametrize(
    "exception, status_code",
    [
        (elasticSearchFunctions.ElasticsearchError("No tags"), 400),
        (elasticSearchFunctions.EmptySearchResultError("No tags"), 404),
    ],
    ids=["Elasticsearch error", "Empty search result error"],
)
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.get_file_tags")
def test_transfer_file_tags_handle_exceptions(
    get_file_tags,
    get_client,
    exception,
    status_code,
    admin_client,
    dashboard_uuid,
    file,
):
    get_file_tags.side_effect = exception
    response = admin_client.get(reverse("file:transfer_file_tags", args=[file.uuid]))
    assert response.status_code == status_code

    assert response.json() == {
        "success": False,
        "message": "No tags",
    }


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch(
    "elasticSearchFunctions.set_file_tags",
    return_value=["test"],
)
def test_transfer_file_tags_if_update_tags(
    set_file_tags, get_client, admin_client, dashboard_uuid, file
):
    tag_to_update = ["new_tag"]
    response = admin_client.put(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_update),
    )
    assert response.status_code == 200

    assert response.json() == {"success": True}


def test_transfer_file_tags_fails_if_no_JSON_document_requested(
    admin_client, dashboard_uuid, file
):
    response = admin_client.put(reverse("file:transfer_file_tags", args=[file.uuid]))
    assert response.status_code == 400

    assert response.json() == {
        "success": False,
        "message": "No JSON document could be decoded from the request.",
    }


def test_transfer_file_tags_fails_if_updated_tag_is_not_list(
    admin_client, dashboard_uuid, file
):
    tag_to_update = "new_tag"
    response = admin_client.put(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_update),
    )
    assert response.status_code == 400

    assert response.json() == {
        "success": False,
        "message": "The request body must be an array.",
    }


@pytest.mark.parametrize(
    "exception, status_code",
    [
        (elasticSearchFunctions.ElasticsearchError("No tags"), 400),
        (elasticSearchFunctions.EmptySearchResultError("No tags"), 404),
    ],
    ids=["Elasticsearch error", "Empty search result error"],
)
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.set_file_tags")
def test_transfer_file_tags_handle_exceptions_if_updating_tags(
    set_file_tags,
    get_client,
    exception,
    status_code,
    admin_client,
    dashboard_uuid,
    file,
):
    tag_to_update = ["new_tag"]
    set_file_tags.side_effect = exception
    response = admin_client.put(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_update),
    )
    assert response.status_code == status_code

    assert response.json() == {
        "success": False,
        "message": "No tags",
    }


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch(
    "elasticSearchFunctions.set_file_tags",
    return_value=["test"],
)
def test_transfer_file_tags_if_tags_are_removed(
    set_file_tags, get_client, admin_client, dashboard_uuid, file
):
    tag_to_delete = ["new_tag"]
    response = admin_client.delete(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_delete),
    )
    assert response.status_code == 200

    assert response.json() == {"success": True}


@pytest.mark.parametrize(
    "exception, status_code",
    [
        (elasticSearchFunctions.ElasticsearchError("No tags"), 400),
        (elasticSearchFunctions.EmptySearchResultError("No tags"), 404),
    ],
    ids=["Elasticsearch error", "Empty search result error"],
)
@mock.patch("elasticSearchFunctions.get_client")
@mock.patch("elasticSearchFunctions.set_file_tags")
def test_transfer_file_tags_handle_exceptions_if_tags_are_removed(
    set_file_tags,
    get_client,
    exception,
    status_code,
    admin_client,
    dashboard_uuid,
    file,
):
    set_file_tags.side_effect = exception
    tag_to_delete = ["new_tag"]
    response = admin_client.delete(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_delete),
    )
    assert response.status_code == status_code

    assert response.json() == {
        "success": False,
        "message": "No tags",
    }
