import os
import shutil
import uuid

import pytest

from archivematica.MCPClient.clientScripts import restructure_dip_for_content_dm_upload

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# UUID of the AIP whose METS the DIP directory fixtures hold.
AIP_UUID = str(uuid.uuid4())


@pytest.fixture
def dip_directory_path(tmp_path):
    result = tmp_path / "dip"
    result.mkdir()
    (result / "objects").mkdir()

    shutil.copy(
        os.path.join(THIS_DIR, "fixtures", "mets_sip_dc.xml"),
        result / f"METS.{AIP_UUID}.xml",
    )

    return result


@pytest.fixture
def dip_directory_with_optional_dc_columns_path(tmp_path):
    result = tmp_path / "dip"
    result.mkdir()
    (result / "objects").mkdir()

    shutil.copy(
        os.path.join(THIS_DIR, "fixtures", "mets_sip_dc_with_optional_columns.xml"),
        result / f"METS.{AIP_UUID}.xml",
    )

    return result


def test_restructure_dip_for_content_dm_upload(mcp_job, dip_directory_path):
    mcp_job.args = (
        None,
        f"--uuid={AIP_UUID}",
        f"--dipDir={dip_directory_path}",
    )
    jobs = [mcp_job]

    restructure_dip_for_content_dm_upload.call(jobs)
    csv_data = (
        (dip_directory_path / "objects/compound.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert not mcp_job.error
    assert mcp_job.get_exit_code() == 0
    assert (
        csv_data[0]
        == "Directory name	title	creator	subject	description	publisher	contributor	date	type	format	identifier	source	relation	language	rights	isPartOf	AIP UUID	file UUID"
    )
    assert (
        csv_data[1]
        == f"objects	Yamani Weapons	Keladry of Mindelan	Glaives	Glaives are cool	Tortall Press	Yuki	2014	Archival Information Package	parchement	42/1; {AIP_UUID}	Numair's library	None	en	Public Domain	AIC#43	{AIP_UUID}	"
    )


def test_restructure_dip_for_content_dm_upload_with_optional_dc_columns(
    mcp_job, dip_directory_with_optional_dc_columns_path
):
    mcp_job.args = (
        None,
        f"--uuid={AIP_UUID}",
        f"--dipDir={dip_directory_with_optional_dc_columns_path}",
    )
    jobs = [mcp_job]

    restructure_dip_for_content_dm_upload.call(jobs)
    csv_data = (
        (dip_directory_with_optional_dc_columns_path / "objects/compound.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert not mcp_job.error
    assert mcp_job.get_exit_code() == 0

    assert (
        csv_data[0]
        == "title\tcreator\tsubject\tdescription\tpublisher\tcontributor\tdate\ttype\tformat\tidentifier\tsource\trelation\tlanguage\trights\tisPartOf\talternative_title\tAIP UUID\tfile UUID\tFilename"
    )
    assert (
        csv_data[1]
        == f"Yamani Weapons\tKeladry of Mindelan\tGlaives; Swords; Blades\tGlaives are cool\tTortall Press\tYuki\t2014\tArchival Information Package\tparchement\t42/1; {AIP_UUID}\tNumair's library\tNone\ten\tPublic Domain\tAIC#43\t\t{AIP_UUID}\t\tobjects"
    )
    assert (
        csv_data[2]
        == f"Evelyn's photo\tEvelyn\t\t\t\t\t\t\t\t{AIP_UUID}\t\t\t\t\tAIC#43\tA photo with Evelyn in it\t{AIP_UUID}\t6e3f5f63-8424-417e-8357-f0a1ea05af62\tevelyn_s_photo-4a4dfb4d-caa3-40ff-99c0-34ed176bb84b.tif"
    )
