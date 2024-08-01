import os

import pytest
import upload_qubit
from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def sip_job(job, sip, tmp_path):
    job_dir = tmp_path / "job"
    job_dir.mkdir()

    job.sipuuid = sip.uuid
    job.jobtype = "Upload DIP"
    job.directory = str(job_dir)
    job.save()

    return job


@pytest.fixture
def access(db, sip):
    return models.Access.objects.create(
        sipuuid=sip.uuid,
        target="atom-description-id",
    )


def test_start_synchronously(db, mocker, mcp_job, sip, sip_job, access):
    mocker.patch(
        "requests.request",
        return_value=mocker.Mock(
            status_code=200, headers={"Location": "http://example.com"}
        ),
    )

    opts = mocker.Mock(
        uuid=sip.uuid,
        rsync_target=False,
        rsync_command=None,
        version=2,
        url="http://example.com",
        email="",
        password="",
        debug=True,
    )

    assert upload_qubit.start(mcp_job, opts) == 0
    assert mcp_job.get_exit_code() == 0

    access = models.Access.objects.get(sipuuid=sip.uuid)
    assert access.statuscode == 14
    assert access.resource == f"{opts.url}/atom-description-id"
    assert access.status == "Deposited synchronously"
    assert access.target == "atom-description-id"


def test_first_run(db, mocker, mcp_job, sip_job, sip, sip_file):
    mocker.patch(
        "requests.request",
        return_value=mocker.Mock(
            status_code=200, headers={"Location": "http://example.com"}
        ),
    )

    opts = mocker.Mock(
        uuid=sip.uuid,
        rsync_target=False,
        rsync_command=None,
        version=2,
        url="http://example.com",
        email="",
        password="",
        debug=True,
    )

    assert upload_qubit.start(mcp_job, opts) == 0
    assert mcp_job.get_exit_code() == 0

    access = models.Access.objects.get(sipuuid=sip.uuid)
    assert access.statuscode == 14
    assert access.resource == f"{opts.url}/atom-description-id"
    assert access.status == "Deposited synchronously"
    assert access.target == "atom-description-id"
