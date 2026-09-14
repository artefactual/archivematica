from unittest import mock

import pytest
from django.db import connection

from archivematica.dashboard.main.models import UnitVariable
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import store_aip

SIP_UUID = "1d98c9a0-4a7c-4c90-8c5d-3485e4bd6fd0"
DIP_UUID = "b735fb7f-1387-45b5-949d-18a6a187a551"


@pytest.fixture(autouse=True)
def mock_close_old_connections(monkeypatch: pytest.MonkeyPatch) -> mock.Mock:
    result = mock.Mock()
    monkeypatch.setattr(store_aip, "close_old_connections", result)
    return result


def store_dip(job: mock.Mock, create_file: object) -> int:
    current_location = {
        "path": "/var/archivematica/sharedDirectory/",
        "resource_uri": "/api/v1/location/currently-processing/",
    }
    with (
        mock.patch.object(
            store_aip.storage_service,
            "get_first_location",
            return_value=current_location,
        ),
        mock.patch.object(
            store_aip.storage_service, "get_file_info", side_effect=IndexError
        ),
        mock.patch.object(store_aip, "uuid4", return_value=DIP_UUID),
        mock.patch.object(store_aip.os.path, "isdir", return_value=False),
        mock.patch.object(store_aip.os.path, "getsize", return_value=123),
        mock.patch.object(store_aip, "_create_file", side_effect=create_file),
    ):
        return store_aip.store_aip(
            job,
            "/api/v1/location/aip-store/",
            "/var/archivematica/sharedDirectory/dip.7z",
            SIP_UUID,
            "test-dip",
            "DIP",
        )


@pytest.mark.django_db(transaction=True)
def test_call_does_not_wrap_storage_service_request_in_transaction() -> None:
    job = mock.Mock(
        args=[
            "storeAIP_v0.0",
            "/api/v1/location/aip-store/",
            "/path/to/aip.7z",
            SIP_UUID,
            "test-aip",
            "SIP",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    def assert_no_transaction(*args: object) -> int:
        assert connection.in_atomic_block is False
        return 0

    with mock.patch.object(store_aip, "store_aip", side_effect=assert_no_transaction):
        store_aip.call([job])

    job.set_status.assert_called_once_with(0)


@pytest.mark.django_db
def test_related_package_is_published_after_dip_storage(
    mock_close_old_connections: mock.Mock,
) -> None:
    job = mock.Mock(spec=Job)

    def create_file(*args: object, **kwargs: object) -> dict[str, str]:
        marker_exists = UnitVariable.objects.filter(
            unituuid=SIP_UUID, variable="relatedPackage"
        ).exists()
        assert marker_exists is False
        return {"status": "UPLOADED"}

    assert store_dip(job, create_file) == 0

    mock_close_old_connections.assert_called_once_with()
    marker = UnitVariable.objects.get(unituuid=SIP_UUID, variable="relatedPackage")
    assert marker.unittype == "SIP"
    assert marker.variablevalue == DIP_UUID


@pytest.mark.django_db
def test_related_package_is_not_published_when_dip_storage_fails(
    mock_close_old_connections: mock.Mock,
) -> None:
    job = mock.Mock(spec=Job)

    def create_file(*args: object, **kwargs: object) -> None:
        raise store_aip.StorageServiceCreateFileError("Storage is unavailable")

    with pytest.raises(Exception, match="DIP creation failed"):
        store_dip(job, create_file)

    mock_close_old_connections.assert_called_once_with()
    marker_exists = UnitVariable.objects.filter(
        unituuid=SIP_UUID, variable="relatedPackage"
    ).exists()
    assert marker_exists is False
