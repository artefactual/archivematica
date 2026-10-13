import io
import logging
import os
import pathlib
import tempfile
from unittest import mock

import pytest

from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import upload_qubit


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
def access(sip):
    return models.Access.objects.create(
        sipuuid=sip.uuid,
        target="atom-description-id",
    )


@pytest.mark.django_db
@mock.patch(
    "requests.request",
    return_value=mock.Mock(status_code=200, headers={"Location": "http://example.com"}),
)
def test_start_synchronously(request, mcp_job, sip, sip_job, access):
    opts = mock.Mock(
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


@pytest.mark.django_db
@mock.patch(
    "requests.request",
    return_value=mock.Mock(status_code=200, headers={"Location": "http://example.com"}),
)
def test_first_run(request, mcp_job, sip_job, sip, sip_file):
    opts = mock.Mock(
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


def fake_rsync(command: list[str], stdout: int, stderr: int) -> mock.Mock:
    """Write the progress that rsync prints with -P and finish after one poll."""
    os.write(
        stdout,
        b"sending incremental file list\n      1,024  50%  512.00kB/s    0:00:10\n",
    )

    return mock.Mock(returncode=0, poll=mock.Mock(side_effect=[None, 0]))


@pytest.mark.django_db
@mock.patch(
    "requests.request",
    return_value=mock.Mock(status_code=200, headers={"Location": "http://example.com"}),
)
@mock.patch("time.sleep")
@mock.patch("subprocess.Popen", side_effect=fake_rsync)
def test_start_closes_the_rsync_output_file(
    popen: mock.MagicMock,
    sleep: mock.MagicMock,
    request: mock.MagicMock,
    mcp_job: Job,
    sip: models.SIP,
    sip_job: models.Job,
    access: models.Access,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    opts = mock.Mock(
        uuid=sip.uuid,
        rsync_target="user@host:~/dips/",
        rsync_command=None,
        version=2,
        url="http://example.com",
        email="",
        password="",
        debug=True,
    )
    # The rsync output file is kept after the upload, so create it under tmp_path.
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    caplog.set_level(logging.ERROR, logger=upload_qubit.logger.name)
    # A module global named open shadows the builtin inside upload_qubit, so the
    # test keeps a reference to every file the script opens by name.
    opened: list[io.TextIOWrapper] = []

    def tracking_open(file: str) -> io.TextIOWrapper:
        handle = open(file)
        opened.append(handle)
        return handle

    monkeypatch.setattr(upload_qubit, "open", tracking_open, raising=False)

    assert upload_qubit.start(mcp_job, opts) == 0

    popen.assert_called_once()
    rsync_output = popen.call_args.kwargs["stdout"]
    assert popen.call_args.args == (
        [
            "rsync",
            "--protect-args",
            "-rltz",
            "-P",
            "--chmod=ugo=rwX",
            sip_job.directory,
            opts.rsync_target,
        ],
    )
    assert popen.call_args.kwargs["stderr"] == rsync_output
    assert f"{upload_qubit.PREFIX} Sending... 50 (ETA: 0:00:10)" in caplog.messages
    assert [handle.closed for handle in opened] == [True]
    with pytest.raises(OSError):
        os.fstat(rsync_output)

    access.refresh_from_db()
    assert access.exitcode == 0
    assert access.statuscode == 14
