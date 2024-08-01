import os
import shutil

import parse_external_mets
import pytest
from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def transfer_directory_path(transfer_directory_path):
    (transfer_directory_path / "objects").mkdir()
    (transfer_directory_path / "metadata").mkdir()

    shutil.copy(
        os.path.join(THIS_DIR, "fixtures", "mets_sip_dc.xml"),
        str(
            transfer_directory_path
            / "metadata/METS.a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3.xml"
        ),
    )

    return transfer_directory_path


def test_mets_not_found(mcp_job, transfer_directory_path):
    (
        transfer_directory_path
        / "metadata/METS.a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3.xml"
    ).unlink()

    exit_code = parse_external_mets.main(
        mcp_job, "a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3", str(transfer_directory_path)
    )
    error = mcp_job.error

    # It does not fail but the error is recorded.
    assert error == "[Errno 17] No METS file found in {}\n".format(
        transfer_directory_path / "metadata"
    )
    assert exit_code == 0


def test_mets_cannot_parse(mcp_job, transfer_directory_path):
    (
        transfer_directory_path
        / "metadata/METS.a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3.xml"
    ).write_text("!!! no xml")

    exit_code = parse_external_mets.main(
        mcp_job, "a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3", str(transfer_directory_path)
    )
    error = str(mcp_job.output)

    # It does not fail but the error is recorded.
    # TODO: why are we not communicating this error?
    assert "Error parsing reingest METS" in error
    assert exit_code == 0


def test_mets_is_parsed(db, mcp_job, transfer_directory_path):
    exit_code = parse_external_mets.main(
        mcp_job, "a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3", str(transfer_directory_path)
    )

    dc_items = models.DublinCore.objects.filter(
        metadataappliestoidentifier="a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3",
        metadataappliestotype_id=models.MetadataAppliesToType.SIP_TYPE,
    )

    assert not mcp_job.error
    assert exit_code == 0

    assert len(dc_items) == 1
    assert dc_items[0].title == "Yamani Weapons"
