import os
import shutil
import uuid

import pytest

from archivematica.dashboard.main import models
from archivematica.MCPClient.clientScripts import parse_external_mets

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# UUID of the SIP whose METS the transfer directory fixture holds.
SIP_UUID = str(uuid.uuid4())


@pytest.fixture
def transfer_directory_path(transfer_directory_path):
    (transfer_directory_path / "objects").mkdir()
    (transfer_directory_path / "metadata").mkdir()

    shutil.copy(
        os.path.join(THIS_DIR, "fixtures", "mets_sip_dc.xml"),
        str(transfer_directory_path / f"metadata/METS.{SIP_UUID}.xml"),
    )

    return transfer_directory_path


def test_mets_not_found(mcp_job, transfer_directory_path):
    (transfer_directory_path / f"metadata/METS.{SIP_UUID}.xml").unlink()

    exit_code = parse_external_mets.main(
        mcp_job, SIP_UUID, str(transfer_directory_path)
    )
    error = mcp_job.error

    # It does not fail but the error is recorded.
    assert error == "[Errno 17] No METS file found in {}\n".format(
        transfer_directory_path / "metadata"
    )
    assert exit_code == 0


def test_mets_cannot_parse(mcp_job, transfer_directory_path):
    (transfer_directory_path / f"metadata/METS.{SIP_UUID}.xml").write_text("!!! no xml")

    exit_code = parse_external_mets.main(
        mcp_job, SIP_UUID, str(transfer_directory_path)
    )
    error = str(mcp_job.output)

    # It does not fail but the error is recorded.
    # TODO: why are we not communicating this error?
    assert "Error parsing reingest METS" in error
    assert exit_code == 0


def test_mets_is_parsed(db, mcp_job, transfer_directory_path):
    models.MetadataAppliesToType.objects.get_or_create(
        pk="3e48343d-e2d2-4956-aaa3-b54d26eb9761", description="SIP"
    )
    exit_code = parse_external_mets.main(
        mcp_job, SIP_UUID, str(transfer_directory_path)
    )

    dc_items = models.DublinCore.objects.filter(
        metadataappliestoidentifier=SIP_UUID,
        metadataappliestotype_id=models.MetadataAppliesToType.SIP_TYPE,
    )

    assert not mcp_job.error
    assert exit_code == 0

    assert len(dc_items) == 1
    assert dc_items[0].title == "Yamani Weapons"
