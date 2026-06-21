from unittest import mock

import pytest

from archivematica.dashboard.main import models
from archivematica.MCPClient.clientScripts import failed_transfer_cleanup


@pytest.mark.django_db
def test_main_tolerates_missing_transfer_path(tmp_path):
    transfer = models.Transfer.objects.create(type="standard")
    job = mock.Mock()
    missing_path = tmp_path / "missing-transfer"

    with mock.patch.object(failed_transfer_cleanup.metrics, "transfer_failed") as metric:
        result = failed_transfer_cleanup.main(
            job,
            failed_transfer_cleanup.FAILED,
            transfer.uuid,
            str(missing_path),
            allow_missing_path=True,
        )

    assert result == 0
    job.pyprint.assert_any_call(
        "Transfer path does not exist or is not a directory; "
        "skipping reingest cleanup:",
        str(missing_path),
    )
    metric.assert_called_once_with("standard", failed_transfer_cleanup.FAILED)


@pytest.mark.django_db
def test_main_rejects_missing_transfer_path_by_default(tmp_path):
    job = mock.Mock()
    missing_path = tmp_path / "missing-transfer"

    with pytest.raises(FileNotFoundError):
        failed_transfer_cleanup.main(
            job,
            failed_transfer_cleanup.FAILED,
            "unused-transfer-uuid",
            str(missing_path),
        )
