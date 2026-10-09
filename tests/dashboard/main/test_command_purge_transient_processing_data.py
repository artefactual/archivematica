import uuid
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from django.utils.dateparse import parse_duration

import archivematica.search.constants
from archivematica.dashboard.main import models
from archivematica.search.service import SearchServiceError
from tests.factories import TransferFactory


@pytest.fixture
def search_disabled(settings):
    settings.SEARCH_ENABLED = []


@pytest.fixture
def search_enabled(settings):
    settings.SEARCH_ENABLED = [
        archivematica.search.constants.AIPS_INDEX,
    ]


@pytest.fixture()
def old_transfer(transfer):
    transfer.completed_at = timezone.now() - parse_duration("0 12:00:00")
    transfer.save()

    return transfer


@pytest.fixture()
def old_sip(sip):
    sip.completed_at = timezone.now() - parse_duration("0 12:00:00")
    sip.save()

    return sip


@pytest.mark.django_db
def test_purge_command_removes_package_with_unknown_status(
    search_disabled, old_transfer
):
    models.Transfer.objects.filter(pk=old_transfer.pk).update(
        status=models.PACKAGE_STATUS_UNKNOWN
    )

    call_command("purge_transient_processing_data", "--purge-unknown")

    assert models.Transfer.objects.filter(pk=old_transfer.pk).count() == 0


@pytest.mark.django_db
def test_purge_command_keeps_package_with_failed_status(search_disabled, old_transfer):
    models.Transfer.objects.filter(pk=old_transfer.pk).update(
        status=models.PACKAGE_STATUS_FAILED
    )

    call_command("purge_transient_processing_data", "--keep-failed")

    assert models.Transfer.objects.filter(pk=old_transfer.pk).count() == 1


@pytest.mark.django_db
def test_purge_command_skips_recent_packages(search_disabled, transfer):
    call_command("purge_transient_processing_data", "--age", "0 06:00:00")

    assert models.Transfer.objects.filter(pk=transfer.pk).count() == 1


@pytest.mark.django_db
def test_purge_command_removes_package_matching_age_criteria(
    search_disabled, old_transfer
):
    call_command("purge_transient_processing_data", "--age", "0 06:00:00")

    assert models.Transfer.objects.filter(pk=old_transfer.pk).count() == 0


@pytest.mark.django_db
def test_purge_command_removes_all_packages(
    search_disabled, transfer, old_transfer, sip, old_sip
):
    call_command("purge_transient_processing_data", "--age", "0")

    assert models.Transfer.objects.all().count() == 0
    assert models.SIP.objects.all().count() == 0


@pytest.mark.django_db
def test_purge_command_removes_search_documents(
    mock_search_service,
    search_enabled,
    old_sip,
):
    call_command("purge_transient_processing_data")

    mock_search_service.delete_aip.assert_called_once_with(str(old_sip.uuid))
    mock_search_service.delete_aip_files.assert_called_once_with(str(old_sip.uuid))


@pytest.mark.django_db
def test_purge_command_reports_search_errors_and_continues(
    mock_search_service, search_enabled, old_sip, old_transfer, capsys
):
    mock_search_service.delete_aip.side_effect = SearchServiceError("boom")

    call_command("purge_transient_processing_data")

    captured = capsys.readouterr()
    assert "Error: boom" in captured.out
    assert "SearchServiceError: boom" in captured.out
    assert models.Transfer.objects.filter(pk=old_transfer.pk).count() == 0


@pytest.mark.django_db
def test_purge_command_keeps_search_documents(
    mock_search_service,
    search_enabled,
    old_transfer,
):
    call_command("purge_transient_processing_data", "--keep-searches")

    mock_search_service.delete_aip.assert_not_called()
    mock_search_service.delete_aip_files.assert_not_called()


@pytest.mark.django_db
def test_purge_command_skips_active_packages(
    search_disabled: None,
    old_transfer: models.Transfer,
    old_sip: models.SIP,
    capsys: pytest.CaptureFixture[str],
    make_transfer: TransferFactory,
) -> None:
    make_transfer(status=models.PACKAGE_STATUS_PROCESSING)

    call_command("purge_transient_processing_data")

    # We've created three packages, but only 1 is in active state.
    assert models.Transfer.objects.all().count() == 1
    assert models.SIP.objects.all().count() == 0


@pytest.mark.django_db
def test_purge_command_output(search_disabled, old_transfer, old_sip, capsys):
    call_command("purge_transient_processing_data")
    captured = capsys.readouterr()

    assert "Transfer %s with status Done" % old_transfer.pk in captured.out
    assert "SIP %s with status Done" % old_sip.pk in captured.out


@pytest.mark.django_db
def test_purge_command_removes_only_expired_idempotency_records(search_disabled):
    expired = models.IdempotencyRecord.objects.create(
        user_id=1,
        operation="package.create",
        key_hash="a" * 64,
        request_fingerprint="b" * 64,
        result={"id": str(uuid.uuid4())},
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    active = models.IdempotencyRecord.objects.create(
        user_id=1,
        operation="package.create",
        key_hash="c" * 64,
        request_fingerprint="d" * 64,
        result={"id": str(uuid.uuid4())},
        expires_at=timezone.now() + timedelta(days=1),
    )

    call_command("purge_transient_processing_data", "--keep-failed")

    assert not models.IdempotencyRecord.objects.filter(pk=expired.pk).exists()
    assert models.IdempotencyRecord.objects.filter(pk=active.pk).exists()


@pytest.mark.django_db
def test_purge_command_dry_run_keeps_expired_idempotency_records(search_disabled):
    record = models.IdempotencyRecord.objects.create(
        user_id=1,
        operation="package.create",
        key_hash="a" * 64,
        request_fingerprint="b" * 64,
        result={"id": str(uuid.uuid4())},
        expires_at=timezone.now() - timedelta(seconds=1),
    )

    call_command("purge_transient_processing_data", "--dry-run")

    assert models.IdempotencyRecord.objects.filter(pk=record.pk).exists()
