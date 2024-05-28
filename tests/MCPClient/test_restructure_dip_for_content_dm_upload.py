import os
import shutil

import pytest
import restructure_dip_for_content_dm_upload
from client.job import Job

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def job():
    return Job("stub", "stub", [])


@pytest.fixture
def dip_directory(tmpdir):
    shutil.copy(
        os.path.join(THIS_DIR, "fixtures", "mets_sip_dc.xml"),
        str(tmpdir / "METS.a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3.xml"),
    )
    (tmpdir / "objects").mkdir()

    return tmpdir


@pytest.fixture
def dip_directory_optional_dc_columns(tmpdir):
    shutil.copy(
        os.path.join(THIS_DIR, "fixtures", "mets_sip_dc_with_optional_columns.xml"),
        str(tmpdir / "METS.a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3.xml"),
    )
    (tmpdir / "objects").mkdir()

    return tmpdir


def test_restructure_dip_for_content_dm_upload(job, dip_directory):
    job.args = (
        None,
        "--uuid=a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3",
        f"--dipDir={dip_directory}",
    )
    jobs = [job]

    restructure_dip_for_content_dm_upload.call(jobs)
    csv_data = (
        (dip_directory / "objects/compound.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert not job.error
    assert job.get_exit_code() == 0
    assert (
        csv_data[0]
        == "Directory name	title	creator	subject	description	publisher	contributor	date	type	format	identifier	source	relation	language	rights	isPartOf	AIP UUID	file UUID"
    )
    assert (
        csv_data[1]
        == "objects	Yamani Weapons	Keladry of Mindelan	Glaives	Glaives are cool	Tortall Press	Yuki	2014	Archival Information Package	parchement	42/1; a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3	Numair's library	None	en	Public Domain	AIC#43	a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3	"
    )


def test_restructure_dip_for_content_dm_upload_with_optional_dc_columns(
    job, dip_directory_optional_dc_columns
):
    job.args = (
        None,
        "--uuid=a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3",
        f"--dipDir={dip_directory_optional_dc_columns}",
    )
    jobs = [job]

    restructure_dip_for_content_dm_upload.call(jobs)
    csv_data = (
        (dip_directory_optional_dc_columns / "objects/compound.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert not job.error
    assert job.get_exit_code() == 0

    assert (
        csv_data[0]
        == "title\tcreator\tsubject\tdescription\tpublisher\tcontributor\tdate\ttype\tformat\tidentifier\tsource\trelation\tlanguage\trights\tisPartOf\talternative_title\tAIP UUID\tfile UUID\tFilename"
    )
    assert (
        csv_data[1]
        == "Yamani Weapons\tKeladry of Mindelan\tGlaives; Swords; Blades\tGlaives are cool\tTortall Press\tYuki\t2014\tArchival Information Package\tparchement\t42/1; a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3\tNumair's library\tNone\ten\tPublic Domain\tAIC#43\t\ta2f1f249-7bd4-4f52-8f1a-84319cb1b6d3\t\tobjects"
    )
    assert (
        csv_data[2]
        == "Evelyn's photo\tEvelyn\t\t\t\t\t\t\t\ta2f1f249-7bd4-4f52-8f1a-84319cb1b6d3\t\t\t\t\tAIC#43\tA photo with Evelyn in it\ta2f1f249-7bd4-4f52-8f1a-84319cb1b6d3\t6e3f5f63-8424-417e-8357-f0a1ea05af62\tevelyn_s_photo-4a4dfb4d-caa3-40ff-99c0-34ed176bb84b.tif"
    )
