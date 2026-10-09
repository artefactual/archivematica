"""Regression tests for cleanup before transfer content is materialized."""

import pathlib
from unittest import mock

import pytest

from archivematica.MCPClient.clientScripts import failed_transfer_cleanup
from tests.factories import TransferFactory
from tests.MCPClient.factories import MCPJobFactory


@pytest.mark.django_db
def test_call_tolerates_missing_transfer_path_when_requested(
    tmp_path: pathlib.Path, make_transfer: TransferFactory, make_mcp_job: MCPJobFactory
) -> None:
    """The retrieval-only flag lets failure routing finish without a path."""
    transfer = make_transfer(type="standard")
    missing_path = tmp_path / "missing-transfer"
    job = make_mcp_job(
        [
            failed_transfer_cleanup.FAILED,
            str(transfer.uuid),
            str(missing_path),
            "--allow-missing-path",
        ],
        name="failedtransfercleanup",
        uuid="task-uuid",
    )

    with mock.patch.object(
        failed_transfer_cleanup.metrics, "transfer_failed"
    ) as metric:
        failed_transfer_cleanup.call([job])

    assert job.get_exit_code() == 0
    assert job.get_stdout() == (
        "Transfer path does not exist or is not a directory; "
        f"skipping reingest cleanup: {missing_path}\n"
        "AIP UUID for this Transfer is None\n"
    )
    metric.assert_called_once_with("standard", failed_transfer_cleanup.FAILED)


def test_main_rejects_missing_transfer_path_by_default(tmp_path):
    """Existing cleanup callers retain their strict missing-path behavior."""
    job = mock.Mock()
    missing_path = tmp_path / "missing-transfer"

    with (
        mock.patch.object(
            failed_transfer_cleanup.storage_service, "_storage_api_session"
        ),
        pytest.raises(FileNotFoundError),
    ):
        failed_transfer_cleanup.main(
            job,
            failed_transfer_cleanup.FAILED,
            "unused-transfer-uuid",
            str(missing_path),
        )
