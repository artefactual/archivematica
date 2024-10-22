import uuid
from unittest import mock

import pytest
import pytest_django
import requests
from components import helpers
from django.contrib.auth.models import User
from django.http import HttpResponseNotFound
from django.test import Client
from django.urls import reverse
from main.models import Report
from tastypie.models import ApiKey


@pytest.fixture
@pytest.mark.django_db
def dashboard_uuid() -> str:
    value = str(uuid.uuid4())
    helpers.set_setting("dashboard_uuid", value)

    return value


@pytest.mark.django_db
def test_admin_set_language(dashboard_uuid: str, admin_client: Client) -> None:
    response = admin_client.get(reverse("administration:admin_set_language"))
    assert response.status_code == 200

    assert (
        "Select one of the following languages available:" in response.content.decode()
    )


@pytest.mark.django_db
def test_failure_report_delete(dashboard_uuid: str, admin_client: Client) -> None:
    report = Report.objects.create(content="my report")

    response = admin_client.post(
        reverse("administration:failure_report_delete", args=[report.pk]),
        {"__confirm__": "1"},
        follow=True,
    )
    assert response.status_code == 200

    assert "No reports found." in response.content.decode()
    assert Report.objects.count() == 0


@pytest.mark.django_db
def test_failure_report(dashboard_uuid: str, admin_client: Client) -> None:
    report = Report.objects.create(content="my report")

    response = admin_client.get(reverse("administration:reports_failures_index"))
    assert response.status_code == 200

    content = response.content.decode()
    assert "<h3>Failure report</h3>" in content
    assert reverse("administration:failure_report", args=[report.pk]) in content


@pytest.fixture
def site_url() -> str:
    value = "https://example.com/"
    helpers.set_setting("site_url", value)

    return value


@pytest.fixture
def storage_service_url() -> str:
    value = "https://ss.example.com/"
    helpers.set_setting("storage_service_url", value)

    return value


@pytest.fixture
def storage_service_user() -> str:
    value = "test"
    helpers.set_setting("storage_service_user", value)

    return value


@pytest.fixture
def storage_service_apikey() -> str:
    value = "api-key"
    helpers.set_setting("storage_service_apikey", value)

    return value


@pytest.fixture
def checksum_type() -> str:
    value = "md5"
    helpers.set_setting("checksum_type", value)

    return value


@pytest.mark.django_db
@mock.patch(
    "requests.Session.get",
    side_effect=[mock.Mock(status_code=200, spec=requests.Response)],
)
def test_general_view_renders_initial_dashboard_settings(
    get: mock.Mock,
    dashboard_uuid: str,
    site_url: str,
    storage_service_url: str,
    storage_service_user: str,
    storage_service_apikey: str,
    checksum_type: str,
    admin_client: Client,
) -> None:
    response = admin_client.get(reverse("administration:general"))
    assert response.status_code == 200

    content = response.content.decode()
    assert f"<b>Dashboard UUID</b> {dashboard_uuid}" in content
    assert f'name="general-site_url" value="{site_url}"' in content
    assert (
        f'name="storage-storage_service_url" value="{storage_service_url}"' in content
    )
    assert (
        f'name="storage-storage_service_user" value="{storage_service_user}"' in content
    )
    assert (
        f'name="storage-storage_service_apikey" value="{storage_service_apikey}"'
        in content
    )
    assert f'<option value="{checksum_type}" selected>' in content


@pytest.mark.django_db
@mock.patch("requests.Session.get")
def test_general_view_renders_warning_if_it_cannot_connect_to_pipeline(
    get: mock.Mock,
    dashboard_uuid: str,
    admin_client: Client,
) -> None:
    error = "connection refused"
    get.side_effect = [requests.exceptions.ConnectionError(error)]

    response = admin_client.get(reverse("administration:general"))
    assert response.status_code == 200

    content = response.content.decode()
    assert "Storage Service inaccessible" in content
    assert error in content


@pytest.mark.django_db
@mock.patch(
    "requests.Session.get",
    side_effect=[mock.Mock(status_code=200, spec=requests.Response)],
)
def test_general_view_updates_dashboard_settings(
    get: mock.Mock,
    dashboard_uuid: str,
    site_url: str,
    storage_service_url: str,
    storage_service_user: str,
    storage_service_apikey: str,
    checksum_type: str,
    admin_client: Client,
) -> None:
    new_site_url = "https://other.example.com"
    new_storage_service_url = "https://other.ss.example.com"
    new_storage_service_user = "foobar"
    new_storage_service_apikey = "foobar"
    new_checksum_type = "sha512"

    data = {
        "general-site_url": new_site_url,
        "storage-storage_service_url": new_storage_service_url,
        "storage-storage_service_user": new_storage_service_user,
        "storage-storage_service_apikey": new_storage_service_apikey,
        "checksum algorithm-checksum_type": new_checksum_type,
    }

    response = admin_client.post(reverse("administration:general"), data)
    assert response.status_code == 200

    assert "Saved" in response.content.decode()
    assert helpers.get_setting("site_url", new_site_url)
    assert helpers.get_setting("storage_service_url", new_storage_service_url)
    assert helpers.get_setting("storage_service_user", new_storage_service_user)
    assert helpers.get_setting("storage_service_apikey", new_storage_service_apikey)
    assert helpers.get_setting("checksum_type", new_checksum_type)


class NotFound(Exception):
    response = HttpResponseNotFound()


@pytest.fixture
def admin_user_apikey(admin_user: User) -> ApiKey:
    return ApiKey.objects.create(user=admin_user)


@pytest.mark.django_db
@mock.patch("storageService.get_pipeline", side_effect=NotFound)
@mock.patch("requests.Session.post")
@mock.patch("platform.node")
def test_general_view_registers_pipeline_in_storage_service(
    node: mock.Mock,
    post: mock.Mock,
    get_pipeline: mock.Mock,
    dashboard_uuid: str,
    site_url: str,
    storage_service_url: str,
    storage_service_user: str,
    storage_service_apikey: str,
    admin_client: Client,
    admin_user: User,
    admin_user_apikey: ApiKey,
    caplog: pytest.LogCaptureFixture,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    hostname = "myhost"
    node.return_value = hostname
    data = {
        "storage-storage_service_url": storage_service_url,
        "storage-storage_service_user": storage_service_user,
        "storage-storage_service_apikey": storage_service_apikey,
        "storage-storage_service_use_default_config": True,
    }
    shared_directory = "/tmp"
    settings.SHARED_DIRECTORY = shared_directory

    response = admin_client.post(reverse("administration:general"), data)
    assert response.status_code == 200

    assert "SS inaccessible or pipeline not registered." in [
        r.message for r in caplog.records
    ]
    post.assert_called_once_with(
        f"{storage_service_url}api/v2/pipeline/",
        json={
            "uuid": dashboard_uuid,
            "description": f"Archivematica on {hostname}",
            "create_default_locations": True,
            "shared_path": shared_directory,
            "remote_name": site_url,
            "api_username": admin_user.username,
            "api_key": admin_user_apikey.key,
        },
    )
