"""Tests for the MCPClient transfer-source retrieval task boundary."""

import uuid
from unittest import mock

import pytest

from archivematica.archivematicaCommon.transfer_source_retrieval import (
    TransferSourceRetrievalError,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    TransferSourceRetrievalResult,
)
from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import retrieve_transfer_source


@pytest.fixture
def retrieval_job(settings):
    """Build a client Job with the arguments emitted by workflow.json."""

    def make(transfer_uuid):
        return Job(
            "retrievetransfersource_v0.0",
            "task-uuid",
            [
                str(transfer_uuid),
                "source-loc:/transfer/source/path/.",
                "tmp/tmp123/transfer",
                f"{settings.SHARED_DIRECTORY}tmp/tmp123/transfer",
                settings.PROCESSING_DIRECTORY,
                settings.SHARED_DIRECTORY,
            ],
        )

    return make


@pytest.mark.django_db
def test_call_retrieves_transfer_source_and_updates_transfer(
    transfer: models.Transfer,
    settings,
    retrieval_job,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = TransferSourceRetrievalResult(
        final_path=f"{settings.PROCESSING_DIRECTORY}transfer",
        current_location="%sharedPath%currentlyProcessing/transfer",
    )
    retrieve = mock.Mock(return_value=result)
    monkeypatch.setattr(retrieve_transfer_source, "retrieve_transfer_source", retrieve)
    job = retrieval_job(transfer.uuid)

    retrieve_transfer_source.call([job])

    retrieve.assert_called_once_with(
        ["source-loc:/transfer/source/path/."],
        "tmp/tmp123/transfer",
        f"{settings.SHARED_DIRECTORY}tmp/tmp123/transfer",
        settings.PROCESSING_DIRECTORY,
        settings.SHARED_DIRECTORY,
        retrieve_transfer_source.storage_service,
    )
    transfer.refresh_from_db()
    assert transfer.currentlocation == "%sharedPath%currentlyProcessing/transfer"
    assert job.get_exit_code() == 0
    assert job.get_stderr() == ""


@pytest.mark.django_db
def test_call_fails_before_retrieval_when_transfer_does_not_exist(
    retrieval_job, monkeypatch: pytest.MonkeyPatch
) -> None:
    transfer_uuid = uuid.uuid4()
    retrieve = mock.Mock()
    monkeypatch.setattr(retrieve_transfer_source, "retrieve_transfer_source", retrieve)
    job = retrieval_job(transfer_uuid)

    retrieve_transfer_source.call([job])

    retrieve.assert_not_called()
    assert job.get_exit_code() == 1
    assert job.get_stderr() == f"Transfer {transfer_uuid} was not found.\n"


@pytest.mark.django_db
def test_call_reports_invalid_transfer_uuid(
    retrieval_job, monkeypatch: pytest.MonkeyPatch
) -> None:
    retrieve = mock.Mock()
    monkeypatch.setattr(retrieve_transfer_source, "retrieve_transfer_source", retrieve)
    job = retrieval_job("not-a-uuid")

    retrieve_transfer_source.call([job])

    retrieve.assert_not_called()
    assert job.get_exit_code() == 1
    assert "Invalid transfer UUID 'not-a-uuid'" in job.get_stderr()


@pytest.mark.django_db
def test_call_does_not_update_transfer_when_retrieval_fails(
    transfer: models.Transfer,
    retrieval_job,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer.currentlocation = "%sharedPath%currentlyProcessing/original"
    transfer.save()
    retrieve = mock.Mock(
        side_effect=TransferSourceRetrievalError("Storage Service copy timed out")
    )
    monkeypatch.setattr(retrieve_transfer_source, "retrieve_transfer_source", retrieve)
    job = retrieval_job(transfer.uuid)

    retrieve_transfer_source.call([job])

    transfer.refresh_from_db()
    assert transfer.currentlocation == "%sharedPath%currentlyProcessing/original"
    retrieve.assert_called_once()
    assert job.get_exit_code() == 1
    assert job.get_stderr() == "Storage Service copy timed out\n"
