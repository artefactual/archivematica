import uuid
from unittest import mock

import elasticSearchFunctions as es
import pytest
from django.core.management import call_command
from django.utils import timezone
from django.utils.dateparse import parse_duration
from main import models


@pytest.fixture
def search_disabled(settings):
    settings.SEARCH_ENABLED = []


@pytest.fixture
def search_enabled(settings):
    settings.SEARCH_ENABLED = [es.TRANSFERS_INDEX, es.AIPS_INDEX]


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
@mock.patch(
    "main.management.commands.purge_transient_processing_data.es.create_indexes_if_needed"
)
@mock.patch(
    "main.management.commands.purge_transient_processing_data.es.remove_backlog_transfer"
)
@mock.patch(
    "main.management.commands.purge_transient_processing_data.es.remove_backlog_transfer_files"
)
def test_purge_command_removes_search_documents(
    mock_remove_backlog_transfer_files,
    mock_remove_backlog_transfer,
    search_enabled,
    old_transfer,
):
    call_command("purge_transient_processing_data")

    mock_remove_backlog_transfer.assert_called_once_with(mock.ANY, old_transfer.pk)
    mock_remove_backlog_transfer_files.assert_called_once_with(
        mock.ANY, old_transfer.pk
    )


@mock.patch(
    "main.management.commands.purge_transient_processing_data.es.create_indexes_if_needed"
)
@mock.patch(
    "main.management.commands.purge_transient_processing_data.es.remove_backlog_transfer"
)
@mock.patch(
    "main.management.commands.purge_transient_processing_data.es.remove_backlog_transfer_files"
)
@pytest.mark.django_db
def test_purge_command_keeps_search_documents(
    mock_remove_backlog_transfer_files,
    mock_remove_backlog_transfer,
    search_enabled,
    old_transfer,
):
    call_command("purge_transient_processing_data", "--keep-searches")

    mock_remove_backlog_transfer.assert_not_called()
    mock_remove_backlog_transfer_files.assert_not_called()


@pytest.mark.django_db
def test_purge_command_skips_active_packages(
    search_disabled, old_transfer, old_sip, capsys
):
    models.Transfer.objects.create(
        uuid=uuid.uuid4(),
        currentlocation=r"%transferDirectory%",
        status=models.PACKAGE_STATUS_PROCESSING,
    )

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
