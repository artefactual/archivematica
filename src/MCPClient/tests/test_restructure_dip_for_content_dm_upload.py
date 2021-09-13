# -*- coding: utf8
from __future__ import unicode_literals

import os
import shutil

import pytest

from client.job import Job

import restructure_dip_for_content_dm_upload


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


def test_restructure_dip_for_content_dm_upload(job, dip_directory):
    job.args = (
        None,
        "--uuid=a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3",
        "--dipDir={}".format(dip_directory),
    )
    jobs = [job]

    restructure_dip_for_content_dm_upload.call(jobs)
    csv_data = (
        (dip_directory / "objects/compound.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert job.error.getbuffer().nbytes == 0
    assert job.get_exit_code() == 0
    assert (
        csv_data[0]
        == "Directory name	title	creator	subject	description	publisher	contributor	date	type	format	identifier	source	relation	language	rights	isPartOf	AIP UUID	file UUID"
    )
    assert (
        csv_data[1]
        == "objects	Yamani Weapons	Keladry of Mindelan	Glaives	Glaives are cool	Tortall Press	Yuki	2014	Archival Information Package	parchement	42/1; a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3	Numair's library	None	en	Public Domain	AIC#43	a2f1f249-7bd4-4f52-8f1a-84319cb1b6d3	"
    )
