import pathlib
from unittest import mock

import pytest
from django.db import connection

from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import verify_aip


@pytest.mark.django_db(transaction=True)
def test_call_does_not_wrap_verification_in_transaction() -> None:
    job = mock.Mock(JobContext=mock.MagicMock(), spec=Job)

    def assert_no_transaction(job: Job) -> int:
        assert connection.in_atomic_block is False
        return 0

    with mock.patch.object(verify_aip, "verify_aip", side_effect=assert_no_transaction):
        verify_aip.call([job])

    job.set_status.assert_called_once_with(0)


@pytest.mark.django_db(transaction=True)
def test_write_premis_event_rolls_back_partial_writes(
    sip_file: models.File,
) -> None:
    job = mock.Mock(spec=Job)

    with mock.patch.object(
        models.Event.agents.related_manager_cls,
        "add",
        side_effect=RuntimeError("agent relationship write failed"),
    ):
        result = verify_aip.write_premis_event(
            job,
            str(sip_file.uuid),
            "sha256",
            "Pass",
            "Checksums match.",
        )

    assert result is None
    assert not models.Event.objects.filter(
        file_uuid=sip_file,
        event_type="fixity check",
    ).exists()
    job.pyprint.assert_called_once_with(
        "Failed to write PREMIS event to database. Error: "
        "agent relationship write failed"
    )


def test_verify_aip_refreshes_connection_before_database_access(
    tmp_path: pathlib.Path,
) -> None:
    sip_uuid = "5ea334b3-e44b-45f9-88e4-15b8e5619b81"
    aip_path = tmp_path / "aip"
    aip_path.mkdir()
    job = mock.Mock(
        args=["verifyAIP_v1.0", sip_uuid, str(aip_path)],
        spec=Job,
    )
    bag = mock.Mock()
    calls = []
    bag.validate.side_effect = lambda **kwargs: calls.append("validate")

    with (
        mock.patch.object(verify_aip, "Bag", return_value=bag),
        mock.patch.object(
            verify_aip,
            "close_old_connections",
            side_effect=lambda: calls.append("close_old_connections"),
        ),
        mock.patch.object(
            verify_aip,
            "verify_checksums",
            side_effect=lambda *args: calls.append("verify_checksums"),
        ) as verify_checksums,
    ):
        assert verify_aip.verify_aip(job) == 0

    assert calls == ["validate", "close_old_connections", "verify_checksums"]
    bag.validate.assert_called_once_with(completeness_only=True)
    verify_checksums.assert_called_once_with(job, bag, sip_uuid)


def test_verify_aip_refreshes_connection_after_extraction_failure(
    tmp_path: pathlib.Path,
) -> None:
    sip_uuid = "5ea334b3-e44b-45f9-88e4-15b8e5619b81"
    aip_path = tmp_path / "aip.7z"
    aip_path.touch()
    job = mock.Mock(
        args=["verifyAIP_v1.0", sip_uuid, str(aip_path)],
        spec=Job,
    )

    with (
        mock.patch.object(verify_aip, "extract_aip", side_effect=Exception),
        mock.patch.object(verify_aip, "close_old_connections") as close_connections,
    ):
        assert verify_aip.verify_aip(job) == 1

    close_connections.assert_called_once_with()


def test_verify_aip_refreshes_connection_after_bag_failure(
    tmp_path: pathlib.Path,
) -> None:
    sip_uuid = "5ea334b3-e44b-45f9-88e4-15b8e5619b81"
    aip_path = tmp_path / "aip"
    aip_path.mkdir()
    job = mock.Mock(
        args=["verifyAIP_v1.0", sip_uuid, str(aip_path)],
        spec=Job,
    )
    bag = mock.Mock()
    bag.validate.side_effect = verify_aip.BagError("Invalid bag")

    with (
        mock.patch.object(verify_aip, "Bag", return_value=bag),
        mock.patch.object(verify_aip, "close_old_connections") as close_connections,
        mock.patch.object(verify_aip, "verify_checksums") as verify_checksums,
    ):
        assert verify_aip.verify_aip(job) == 1

    close_connections.assert_called_once_with()
    verify_checksums.assert_not_called()
