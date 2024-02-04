import os
import shutil

import parse_external_mets
import pytest
from client.job import Job
from main import models


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def job():
    return Job("stub", "stub", [])


@pytest.fixture
def transfer_dir(tmp_path):
    (tmp_path / "objects").mkdir()
    (tmp_path / "metadata").mkdir()

    shutil.copy(
        os.path.join(THIS_DIR, "fixtures", "mets_sip_dc.xml"),
        str(tmp_path / "metadata/METS.a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3.xml"),
    )

    return tmp_path


def test_mets_not_found(job, transfer_dir):
    (transfer_dir / "metadata/METS.a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3.xml").unlink()

    exit_code = parse_external_mets.main(
        job, "a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3", str(transfer_dir)
    )
    error = job.error

    # It does not fail but the error is recorded.
    assert error == "[Errno 17] No METS file found in {}\n".format(
        transfer_dir / "metadata"
    )
    assert exit_code == 0


def test_mets_cannot_parse(job, transfer_dir):
    (
        transfer_dir / "metadata/METS.a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3.xml"
    ).write_text("!!! no xml")

    exit_code = parse_external_mets.main(
        job, "a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3", str(transfer_dir)
    )
    error = str(job.output)

    # It does not fail but the error is recorded.
    # TODO: why are we not communicating this error?
    assert "Error parsing reingest METS" in error
    assert exit_code == 0


def test_mets_is_parsed(db, job, transfer_dir):
    exit_code = parse_external_mets.main(
        job, "a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3", str(transfer_dir)
    )

    dc_items = models.DublinCore.objects.filter(
        metadataappliestoidentifier="a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3",
        metadataappliestotype_id=models.MetadataAppliesToType.SIP_TYPE,
    )

    assert not job.error
    assert exit_code == 0

    assert len(dc_items) == 1
    assert dc_items[0].title == "Yamani Weapons"
