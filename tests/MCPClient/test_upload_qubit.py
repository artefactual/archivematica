import os
import pickle as pickle
import uuid

import pytest
from client.job import Job
from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

import upload_qubit


@pytest.fixture()
def mcp_job():
    return Job("stub", "stub", [])


@pytest.fixture
def sip(db):
    return models.SIP.objects.create(uuid=str(uuid.uuid4()))


@pytest.fixture
def transfer(db, sip):
    transfer = models.Transfer.objects.create(access_system_id="atom-description-id")
    models.File.objects.create(sip=sip, transfer=transfer)
    return transfer


@pytest.fixture
def job(sip, tmp_path):
    job_dir = tmp_path / "job"
    job_dir.mkdir()
    return models.Job.objects.create(
        sipuuid=sip.uuid,
        jobtype="Upload DIP",
        directory=str(job_dir),
        createdtime="2021-06-29T00:00:00Z",
    )


@pytest.fixture
def access(db, sip):
    return models.Access.objects.create(
        sipuuid=sip.uuid,
        target=pickle.dumps({"target": "atom-description-id"}, protocol=0).decode(),
    )


def test_start_synchronously(db, mocker, mcp_job, sip, job, access):
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
    assert pickle.loads(access.target.encode()) == {"target": "atom-description-id"}


def test_first_run(db, mocker, mcp_job, job, transfer, sip):
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
    assert pickle.loads(access.target.encode()) == {"target": "atom-description-id"}
