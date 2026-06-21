"""Regression tests for moving failed transfers with no materialized source."""

from unittest import mock

import pytest

from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import move_transfer


@pytest.mark.django_db
def test_call_tolerates_missing_source_when_requested(tmp_path):
    """Retrieval failure cleanup is a no-op when no source was copied."""
    transfer = models.Transfer.objects.create(currentlocation="original")
    source = tmp_path / "missing-transfer"
    destination = tmp_path / "failed" / "."
    job = Job(
        "movetransfer_v0.0",
        "task-uuid",
        [
            str(source),
            str(destination),
            str(transfer.uuid),
            str(tmp_path),
            str(transfer.uuid),
            str(tmp_path),
            "--allow-missing-source",
        ],
    )

    with mock.patch.object(move_transfer, "rename") as rename:
        move_transfer.call([job])

    assert job.get_exit_code() == 0
    rename.assert_not_called()
    assert job.get_stdout() == (
        f"Transfer path does not exist; nothing to move: {source}\n"
    )
    transfer.refresh_from_db()
    assert transfer.currentlocation == "original"


@pytest.mark.django_db
def test_call_keeps_missing_source_strict_by_default(tmp_path):
    """The optional tolerance must not alter existing workflow callers."""
    job = Job(
        "movetransfer_v0.0",
        "task-uuid",
        ["source", "destination", "transfer-uuid", str(tmp_path)],
    )

    with mock.patch.object(move_transfer, "moveSIP", return_value=0) as move_sip:
        move_transfer.call([job])

    move_sip.assert_called_once_with(
        job,
        "source",
        "destination",
        "transfer-uuid",
        str(tmp_path),
        allow_missing_source=False,
    )
