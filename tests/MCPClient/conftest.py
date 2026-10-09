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
    transfer_uuid = uuid.uuid4()

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
            size=size,
            checksum=checksum,
            checksumtype="sha256",
        )
        for path, size, checksum in [
            (
                "たくさん directories/need name change/checking here/evélyn's photo.jpg",
                158131,
                photo_checksum,
            ),
            (
                "no_name_change/needed_here/lion.svg",
                18324,
                lion_checksum,
            ),
            (
                "たくさん directories/need name change/checking here/lion写真.svg",
                18324,
                lion_checksum,
            ),
            (
                "has space/lion.svg",
                18324,
                lion_checksum,
            ),
        ]
    ]
