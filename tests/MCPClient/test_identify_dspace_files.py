import pathlib

import pytest

from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import identify_dspace_files

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures" / "dspace"


def _decode_binary_path(value: bytes | memoryview | None) -> str:
    assert isinstance(value, bytes)
    return value.decode()


def _create_transfer_file(
    transfer: models.Transfer, currentlocation: str
) -> models.File:
    return models.File.objects.create(
        transfer=transfer,
        filegrpuse="original",
        originallocation=currentlocation.encode(),
        currentlocation=currentlocation.encode(),
    )


@pytest.mark.django_db
def test_identify_dspace_files_marks_all_license_files_in_filegrp(
    mcp_job: Job, transfer: models.Transfer, transfer_directory_path: pathlib.Path
) -> None:
    relative_dir = transfer_directory_path / "objects" / "item"
    for filename in ("bitstream_8267", "bitstream_8267-2", "bitstream_40314.txt"):
        _create_transfer_file(
            transfer,
            f"%transferDirectory%objects/item/{filename}",
        )

    identify_dspace_files.identify_dspace_files(
        mcp_job,
        str(FIXTURES_DIR / "mets_item_multiple_licenses.xml"),
        f"{transfer_directory_path}/",
        str(transfer.uuid),
        relative_dir=f"{relative_dir}/",
    )

    filegrpuse_by_location = {
        _decode_binary_path(file_.currentlocation): file_.filegrpuse
        for file_ in models.File.objects.filter(transfer=transfer)
    }

    assert filegrpuse_by_location == {
        "%transferDirectory%objects/item/bitstream_8267": "license",
        "%transferDirectory%objects/item/bitstream_8267-2": "license",
        "%transferDirectory%objects/item/bitstream_40314.txt": "text/ocr",
    }
