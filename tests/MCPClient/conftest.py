import importlib.resources
import uuid

import pytest

from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from tests.factories import FileFactory
from tests.factories import TransferFactory
from tests.MCPClient.factories import MCPJobFactory


@pytest.fixture(autouse=True)
def set_xml_catalog_files(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use local XML schemas for validation."""
    monkeypatch.setenv(
        "XML_CATALOG_FILES",
        str(
            importlib.resources.files("archivematica.MCPClient")
            / "assets"
            / "catalog"
            / "catalog.xml"
        ),
    )


@pytest.fixture
def make_mcp_job() -> MCPJobFactory:
    return MCPJobFactory()


@pytest.fixture
def mcp_job(make_mcp_job: MCPJobFactory) -> Job:
    return make_mcp_job()


@pytest.fixture
def unicode_transfer(make_transfer: TransferFactory) -> models.Transfer:
    """A standard transfer whose directory name has non-ASCII characters."""
    transfer_uuid = uuid.UUID("e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6")

    return make_transfer(
        uuid=transfer_uuid,
        type="Standard",
        currentlocation=f"%sharedPath%currentlyProcessing/ユニコード-{transfer_uuid}/",
    )


@pytest.fixture
def unicode_transfer_files(
    make_file: FileFactory, unicode_transfer: models.Transfer
) -> list[models.File]:
    """The original files of the unicode transfer, some with non-ASCII paths."""
    photo_checksum = "d2bed92b73c7090bb30a0b30016882e7069c437488e1513e9deaacbe29d38d92"
    lion_checksum = "f78615cd834f7fb84832177e73f13e3479f5b5b22ae7a9506c7fa0a14fd9df9e"

    return [
        make_file(
            f"objects/{path}",
            transfer=unicode_transfer,
            uuid=uuid.UUID(file_uuid),
            size=size,
            checksum=checksum,
            checksumtype="sha256",
        )
        for file_uuid, path, size, checksum in [
            (
                "47813453-6872-442b-9d65-6515be3c5aa1",
                "たくさん directories/need name change/checking here/evélyn's photo.jpg",
                158131,
                photo_checksum,
            ),
            (
                "60e5c61b-14ef-4e92-89ec-9b9201e68adb",
                "no_name_change/needed_here/lion.svg",
                18324,
                lion_checksum,
            ),
            (
                "791e07ea-ad44-4315-b55b-44ec771e95cf",
                "たくさん directories/need name change/checking here/lion写真.svg",
                18324,
                lion_checksum,
            ),
            (
                "8a1f0b59-cf94-47ef-8078-647b77c8a147",
                "has space/lion.svg",
                18324,
                lion_checksum,
            ),
        ]
    ]
