import json
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
    response = admin_client.get(reverse("file:file_details", args=[file.uuid]))
    assert response.status_code == 200

    content = json.loads(response.content.decode("utf8"))
    assert content["id"] == str(file.uuid)
    assert content["title"] == "LICENSE"


@mock.patch("elasticSearchFunctions.get_client")
@pytest.mark.parametrize(
    "mock_file_info, status_code",
    [
        ("get_transfer_file_info returned no exact results", 404),
        ("unknown error", 500),
    ],
    ids=["no exact results", "unknown error"],
)
def test_file_details_handles_exceptions(
    _get_client, admin_client, dashboard_uuid, file, mocker, mock_file_info, status_code
):
    mocker.patch(
        "elasticSearchFunctions.get_transfer_file_info",
        side_effect=elasticSearchFunctions.ElasticsearchError(mock_file_info),
    )

    response = admin_client.get(reverse("file:file_details", args=[file.uuid]))
    assert response.status_code == status_code

    assert json.loads(response.content.decode("utf8")) == {
        "success": False,
        "message": mock_file_info,
    }


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch(
    "elasticSearchFunctions.get_transfer_file_info",
    return_value={
        "filename": "piiTestDataCreditCardNumbers.txt",
        "relative_path": "test-bulk-extract-a239e3e1-0391-46da-94d7-25a3e8509b45/data/objects/piiTestDataCreditCardNumbers.txt",
        "status": "backlog",
        "size": 0.00026416778564453125,
        "tags": [],
        "file_extension": "txt",
        "bulk_extractor_reports": ["ccn"],
        "format": [
            {"puid": "x-fmt/111", "format": "Generic TXT", "group": "Text (Plain)"}
        ],
    },
)
def test_bulk_extractor_if_missing_reports_exist(
    _get_client, _get_transfer_file_info, admin_client, dashboard_uuid, file, sip
):
    response = admin_client.get(reverse("file:bulk_extractor", args=[file.uuid]))
    assert response.status_code == 400

    assert response.json() == {
        "success": False,
        "message": "Requested file is missing the following requested reports: pii",
    }


@mock.patch("components.file.views.len", side_effect=[0])
def test_bulk_extractor_validates_reports_parameter_with_len_mock(
    _len, admin_client, dashboard_uuid, file
):
    response = admin_client.get(
        reverse("file:bulk_extractor", kwargs={"fileuuid": file.uuid})
    )
    assert response.status_code == 400

    assert json.loads(response.content.decode()) == {
        "success": False,
        "message": "No reports were requested.",
    }


@mock.patch("elasticSearchFunctions.get_client")
@pytest.mark.parametrize(
    "mock_file_info, status_code",
    [
        ("get_transfer_file_info returned no exact results", 404),
        ("unknown error", 500),
    ],
    ids=["no exact results", "unknown error"],
)
def test_bulk_extractor_handles_exceptions(
    _get_client, admin_client, dashboard_uuid, file, mocker, mock_file_info, status_code
):
    mocker.patch(
        "elasticSearchFunctions.get_transfer_file_info",
        side_effect=elasticSearchFunctions.ElasticsearchError(mock_file_info),
    )

    response = admin_client.get(
        reverse("file:bulk_extractor", kwargs={"fileuuid": file.uuid})
    )
    assert response.status_code == status_code

    assert json.loads(response.content.decode("utf8")) == {
        "success": False,
        "message": mock_file_info,
    }


@pytest.mark.django_db
@mock.patch("elasticSearchFunctions.get_client")
def test_bulk_extractor_status_code_200(
    _get_client,
    admin_client,
    dashboard_uuid,
    mocker,
    transfer,
    sip,
):
    file = models.File.objects.create(uuid=uuid.uuid4(), transfer=transfer, sip=sip)
    mocker.patch(
        "elasticSearchFunctions.get_transfer_file_info",
        return_value={
            "filename": "piiTestDataCreditCardNumbers.txt",
            "fileuuid": str(file.uuid),
            "sipuuid": str(sip.uuid),
            "status": "backlog",
            "created": 1713465340.0109284,
            "size": 0.00026416778564453125,
            "tags": [],
            "file_extension": "txt",
            "bulk_extractor_reports": ["ccn", "pii"],
            "format": [
                {"puid": "x-fmt/111", "format": "Generic TXT", "group": "Text (Plain)"}
            ],
            "pending_deletion": False,
        },
    )
    mocker.patch(
        "requests.get",
        return_value=mocker.Mock(
            status_code=200,
            text="""64	378282246310005	rican Express - 378282246310005 02. American E
                                                          104	371449635398431	rican Express - 371449635398431 03. American E
                                                          154	378734493671000	ess Corporate - 378734493671000 04. Australian
                                                          197	5610591081018250	lian BankCard - 5610591081018250 05. Discover -
                                                          230	6011000990139424	 05. Discover - 6011000990139424 06. JCB - 3566
                                                          258	3566002020360505	9424 06. JCB - 3566002020360505 """,
        ),
    )
    response = admin_client.get(
        reverse("file:bulk_extractor", kwargs={"fileuuid": file.uuid})
    )
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch("elasticSearchFunctions.get_client")
def test_bulk_extractor_status_code_other_than_200(
    _get_client, admin_client, dashboard_uuid, mocker, caplog, transfer, sip
):
    file = models.File.objects.create(uuid=uuid.uuid4(), transfer=transfer, sip=sip)
    mocker.patch(
        "elasticSearchFunctions.get_transfer_file_info",
        return_value={
            "filename": "piiTestDataCreditCardNumbers.txt",
            "fileuuid": file.uuid,
            "sipuuid": sip.uuid,
            "status": "backlog",
            "created": 1713465340.0109284,
            "size": 0.00026416778564453125,
            "tags": [],
            "file_extension": "txt",
            "bulk_extractor_reports": ["ccn", "pii"],
            "format": [
                {"puid": "x-fmt/111", "format": "Generic TXT", "group": "Text (Plain)"}
            ],
            "pending_deletion": False,
        },
    )
    mocker.patch(
        "requests.get",
        return_value=mocker.Mock(status_code=500, text="""Internal Server Error"""),
    )
    response = admin_client.get(
        reverse("file:bulk_extractor", kwargs={"fileuuid": file.uuid})
    )
    assert response.status_code == 200

    assert (
        f"Unable to retrieve ccn report for file with UUID {file.uuid}; response: ('Internal Server Error',)"
        in ([rec.message for rec in caplog.records[1::2]])
    )
    assert f"Unable to retrieve ccn report for file with UUID {file.uuid}" in (
        [(rec.message).split(";")[0] for rec in caplog.records[1::2]]
    )
    assert " response: ('Internal Server Error',)" in (
        [(rec.message).split(";")[1] for rec in caplog.records[1::2]]
    )


@mock.patch("elasticSearchFunctions.get_client")
def test_transfer_file_tags(_get_client, admin_client, dashboard_uuid, file, mocker):
    mocker.patch(
        "elasticSearchFunctions.get_file_tags",
        return_value=["test"],
    )
    response = admin_client.get(reverse("file:transfer_file_tags", args=[file.uuid]))
    assert response.status_code == 200

    assert ["test"] == response.json()


@mock.patch("elasticSearchFunctions.get_client")
@pytest.mark.parametrize(
    "exception, status_code",
    [
        (elasticSearchFunctions.ElasticsearchError("No tags"), 400),
        (elasticSearchFunctions.EmptySearchResultError("No tags"), 404),
    ],
    ids=["Elasticsearch error", "Empty search result error"],
)
def test_transfer_file_tags_handles_exceptions(
    _get_client, exception, status_code, admin_client, dashboard_uuid, file, mocker
):
    mocker.patch(
        "elasticSearchFunctions.get_file_tags",
        side_effect=exception,
    )
    response = admin_client.get(reverse("file:transfer_file_tags", args=[file.uuid]))
    assert response.status_code == status_code

    assert json.loads(response.content.decode("utf8")) == {
        "success": False,
        "message": "No tags",
    }


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch(
    "elasticSearchFunctions.set_file_tags",
    return_value=["test"],
)
def test_transfer_file_tags_put_method(
    _get_client, _set_file_tags, admin_client, dashboard_uuid, file
):
    tag_to_update = ["new_tag"]
    response = admin_client.put(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_update),
    )
    assert response.status_code == 200

    assert response.json() == {"success": True}


def test_transfer_file_tags_put_method_status_code_400(
    admin_client, dashboard_uuid, file
):
    response = admin_client.put(reverse("file:transfer_file_tags", args=[file.uuid]))
    assert response.status_code == 400

    assert {
        "success": False,
        "message": "No JSON document could be decoded from the request.",
    } == response.json()


def test_transfer_file_tags_put_method_if_tags_not_list(
    admin_client, dashboard_uuid, file
):
    tag_to_update = "new_tag"
    response = admin_client.put(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_update),
    )
    assert response.status_code == 400

    assert {
        "success": False,
        "message": "The request body must be an array.",
    } == response.json()


@mock.patch("elasticSearchFunctions.get_client")
@pytest.mark.parametrize(
    "exception, status_code",
    [
        (elasticSearchFunctions.ElasticsearchError("No tags"), 400),
        (elasticSearchFunctions.EmptySearchResultError("No tags"), 404),
    ],
    ids=["Elasticsearch error", "Empty search result error"],
)
def test_transfer_file_tags_handles_exceptions_put_method(
    _get_client, exception, status_code, admin_client, dashboard_uuid, file, mocker
):
    tag_to_update = ["new_tag"]
    mocker.patch(
        "elasticSearchFunctions.set_file_tags",
        side_effect=exception,
    )
    response = admin_client.put(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_update),
    )
    assert response.status_code == status_code

    assert json.loads(response.content.decode("utf8")) == {
        "success": False,
        "message": "No tags",
    }


@mock.patch("elasticSearchFunctions.get_client")
@mock.patch(
    "elasticSearchFunctions.set_file_tags",
    return_value=["test"],
)
def test_transfer_file_tags_delete_method(
    _get_client, _set_file_tags, admin_client, dashboard_uuid, file
):
    tag_to_delete = ["new_tag"]
    response = admin_client.delete(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_delete),
    )
    assert response.status_code == 200

    assert response.json() == {"success": True}


@mock.patch("elasticSearchFunctions.get_client")
@pytest.mark.parametrize(
    "exception, status_code",
    [
        (elasticSearchFunctions.ElasticsearchError("No tags"), 400),
        (elasticSearchFunctions.EmptySearchResultError("No tags"), 404),
    ],
    ids=["Elasticsearch error", "Empty search result error"],
)
def test_transfer_file_tags_handles_exceptions_delete_method(
    _get_client, exception, status_code, admin_client, dashboard_uuid, file, mocker
):
    tag_to_delete = ["new_tag"]
    mocker.patch(
        "elasticSearchFunctions.set_file_tags",
        side_effect=exception,
    )
    response = admin_client.delete(
        reverse("file:transfer_file_tags", args=[file.uuid]),
        data=json.dumps(tag_to_delete),
    )
    assert response.status_code == status_code

    assert json.loads(response.content.decode("utf8")) == {
        "success": False,
        "message": "No tags",
    }
