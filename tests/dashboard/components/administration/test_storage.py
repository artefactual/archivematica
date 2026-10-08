from unittest import mock

import pytest
from django.test import Client

pytestmark = pytest.mark.usefixtures("dashboard_uuid")


@pytest.fixture
def locations() -> list[dict[str, object]]:
    """Locations of the pipeline as returned by the Storage Service API."""
    return [
        {
            "uuid": "821d8b48-8b19-42ae-9956-df1d749c21a2",
            "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
            "used": "0",
            "description": None,
            "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
            "enabled": True,
            "quota": None,
            "relative_path": "var/archivematica/sharedDirectory/",
            "purpose": "CP",
            "path": "/var/archivematica/sharedDirectory",
            "resource_uri": "/api/v2/location/821d8b48-8b19-42ae-9956-df1d749c21a2/",
        },
        {
            "uuid": "bad1cfd5-a67a-4791-b4a9-43590727d25f",
            "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
            "used": "0",
            "description": "",
            "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
            "enabled": True,
            "quota": None,
            "relative_path": "home",
            "purpose": "TS",
            "path": "/home",
            "resource_uri": "/api/v2/location/bad1cfd5-a67a-4791-b4a9-43590727d25f/",
        },
        {
            "uuid": "1232e1d5-a67a-4791-b4a9-4359072747bf",
            "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
            "used": "0",
            "description": "",
            "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
            "enabled": False,
            "quota": None,
            "relative_path": "home",
            "purpose": "TS",
            "path": "/home",
            "resource_uri": "/api/v2/location/1232e1d5-a67a-4791-b4a9-4359072747bf/",
        },
        {
            "uuid": "817f9ef7-dcf7-450d-bfeb-7dba00abedd5",
            "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
            "used": "5368709120",
            "description": "Store AIP in standard Archivematica Directory",
            "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
            "enabled": True,
            "quota": "10737418240",
            "relative_path": "var/archivematica/sharedDirectory/www/AIPsStore",
            "purpose": "AS",
            "path": "/var/archivematica/sharedDirectory/www/AIPsStore",
            "resource_uri": "/api/v2/location/817f9ef7-dcf7-450d-bfeb-7dba00abedd5/",
        },
        {
            "uuid": "6e4cf229-e614-436d-9055-839dfe3145a6",
            "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
            "used": "0",
            "description": "Store DIP in standard Archivematica Directory",
            "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
            "enabled": True,
            "quota": None,
            "relative_path": "var/archivematica/sharedDirectory/www/DIPsStore",
            "purpose": "DS",
            "path": "/var/archivematica/sharedDirectory/www/DIPsStore",
            "resource_uri": "/api/v2/location/6e4cf229-e614-436d-9055-839dfe3145a6/",
        },
        {
            "uuid": "b3333b2a-5f3d-4c32-86b4-d334ff80c111",
            "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
            "used": "0",
            "description": "Default AIP recovery",
            "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
            "enabled": True,
            "quota": None,
            "relative_path": "var/archivematica/storage_service/recover",
            "purpose": "AR",
            "path": "/var/archivematica/storage_service/recover",
            "resource_uri": "/api/v2/location/b3333b2a-5f3d-4c32-86b4-d334ff80c111/",
        },
    ]


@mock.patch(
    "archivematica.dashboard.components.administration.views.storage_service.get_location",
    side_effect=Exception(),
)
def test_ss_connection_fail(get_location: mock.MagicMock, admin_client: Client) -> None:
    response = admin_client.get("/administration/storage/")

    assert "Error retrieving locations" in response.content.decode("utf8")


@mock.patch(
    "archivematica.dashboard.components.administration.views.storage_service.get_location"
)
def test_success(
    get_location: mock.MagicMock,
    admin_client: Client,
    locations: list[dict[str, object]],
) -> None:
    get_location.return_value = locations

    response = admin_client.get("/administration/storage/")

    # The currently processing, AIP recovery and disabled locations are not
    # listed. Only the AIP and DIP storage locations show their usage, with
    # the quota formatted as a file size or as unlimited when it is not set.
    assert [
        (
            location["uuid"],
            location["purpose"],
            location["show_usage"],
            location["quota"],
            location["used"],
        )
        for location in response.context["locations"]
    ] == [
        (
            "817f9ef7-dcf7-450d-bfeb-7dba00abedd5",
            "AIP Storage",
            True,
            "10.0\xa0GB",
            "5.0\xa0GB",
        ),
        (
            "6e4cf229-e614-436d-9055-839dfe3145a6",
            "DIP Storage",
            True,
            "unlimited",
            "0\xa0bytes",
        ),
        ("bad1cfd5-a67a-4791-b4a9-43590727d25f", "Transfer Source", False, None, "0"),
    ]
