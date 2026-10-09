import uuid
from unittest import mock

import pytest
from django.test import Client

pytestmark = pytest.mark.usefixtures("dashboard_uuid")


@pytest.fixture
def locations() -> list[dict[str, object]]:
    """Locations of the pipeline as returned by the Storage Service API."""
    pipeline = f"/api/v2/pipeline/{uuid.uuid4()}/"
    space = f"/api/v2/space/{uuid.uuid4()}/"
    processing_uuid = str(uuid.uuid4())
    transfer_source_uuid = str(uuid.uuid4())
    disabled_transfer_source_uuid = str(uuid.uuid4())
    aip_storage_uuid = str(uuid.uuid4())
    dip_storage_uuid = str(uuid.uuid4())
    aip_recovery_uuid = str(uuid.uuid4())
    return [
        {
            "uuid": processing_uuid,
            "pipeline": [pipeline],
            "used": "0",
            "description": None,
            "space": space,
            "enabled": True,
            "quota": None,
            "relative_path": "var/archivematica/sharedDirectory/",
            "purpose": "CP",
            "path": "/var/archivematica/sharedDirectory",
            "resource_uri": f"/api/v2/location/{processing_uuid}/",
        },
        {
            "uuid": transfer_source_uuid,
            "pipeline": [pipeline],
            "used": "0",
            "description": "",
            "space": space,
            "enabled": True,
            "quota": None,
            "relative_path": "home",
            "purpose": "TS",
            "path": "/home",
            "resource_uri": f"/api/v2/location/{transfer_source_uuid}/",
        },
        {
            "uuid": disabled_transfer_source_uuid,
            "pipeline": [pipeline],
            "used": "0",
            "description": "",
            "space": space,
            "enabled": False,
            "quota": None,
            "relative_path": "home",
            "purpose": "TS",
            "path": "/home",
            "resource_uri": f"/api/v2/location/{disabled_transfer_source_uuid}/",
        },
        {
            "uuid": aip_storage_uuid,
            "pipeline": [pipeline],
            "used": "5368709120",
            "description": "Store AIP in standard Archivematica Directory",
            "space": space,
            "enabled": True,
            "quota": "10737418240",
            "relative_path": "var/archivematica/sharedDirectory/www/AIPsStore",
            "purpose": "AS",
            "path": "/var/archivematica/sharedDirectory/www/AIPsStore",
            "resource_uri": f"/api/v2/location/{aip_storage_uuid}/",
        },
        {
            "uuid": dip_storage_uuid,
            "pipeline": [pipeline],
            "used": "0",
            "description": "Store DIP in standard Archivematica Directory",
            "space": space,
            "enabled": True,
            "quota": None,
            "relative_path": "var/archivematica/sharedDirectory/www/DIPsStore",
            "purpose": "DS",
            "path": "/var/archivematica/sharedDirectory/www/DIPsStore",
            "resource_uri": f"/api/v2/location/{dip_storage_uuid}/",
        },
        {
            "uuid": aip_recovery_uuid,
            "pipeline": [pipeline],
            "used": "0",
            "description": "Default AIP recovery",
            "space": space,
            "enabled": True,
            "quota": None,
            "relative_path": "var/archivematica/storage_service/recover",
            "purpose": "AR",
            "path": "/var/archivematica/storage_service/recover",
            "resource_uri": f"/api/v2/location/{aip_recovery_uuid}/",
        },
    ]


@pytest.mark.django_db
@mock.patch(
    "archivematica.dashboard.components.administration.views.storage_service.get_location",
    side_effect=Exception(),
)
def test_ss_connection_fail(get_location: mock.MagicMock, admin_client: Client) -> None:
    response = admin_client.get("/administration/storage/")

    assert "Error retrieving locations" in response.content.decode("utf8")


@pytest.mark.django_db
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
            locations[3]["uuid"],
            "AIP Storage",
            True,
            "10.0\xa0GB",
            "5.0\xa0GB",
        ),
        (
            locations[4]["uuid"],
            "DIP Storage",
            True,
            "unlimited",
            "0\xa0bytes",
        ),
        (locations[1]["uuid"], "Transfer Source", False, None, "0"),
    ]
