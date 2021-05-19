from datetime import timedelta
import uuid

from django.core.management import call_command
from django.utils import timezone
import pytest

import elasticSearchFunctions as es
from main import models


@pytest.fixture
def search_disabled(settings):
    settings.SEARCH_ENABLED = []


@pytest.fixture
def search_enabled(settings):
    settings.SEARCH_ENABLED = [es.TRANSFERS_INDEX, es.AIPS_INDEX]


@pytest.fixture
def transfer(db):
    transfer = models.Transfer.objects.create(
        uuid=uuid.uuid4(),
        currentlocation=r"%transferDirectory%",
        status=models.PACKAGE_STATUS_DONE,
        completed_at=timezone.now(),
    )

    models.Job.objects.create(
        sipuuid=transfer.pk, unittype="unitTransfer", createdtime=timezone.now()
    )
    models.File.objects.create(uuid=uuid.uuid4(), transfer=transfer)

    return transfer


@pytest.fixture
def sip(db):
    sip = models.SIP.objects.create(
        uuid=uuid.uuid4(),
        status=models.PACKAGE_STATUS_DONE,
        completed_at=timezone.now(),
    )

    models.Job.objects.create(
        sipuuid=sip.pk, unittype="unitSIP", createdtime=timezone.now()
    )
    models.File.objects.create(uuid=uuid.uuid4(), sip=sip)
    models.Access.objects.create(sipuuid=sip.pk)

    return sip


@pytest.mark.django_db
def test_purge_command_removes_package_with_unknown_status(search_disabled, transfer):
    models.Transfer.objects.filter(pk=transfer.pk).update(
        status=models.PACKAGE_STATUS_UNKNOWN
    )

    call_command("purge_transient_processing_data", "--purge-unknown")

    assert models.Transfer.objects.filter(pk=transfer.pk).count() == 0


@pytest.mark.django_db
def test_purge_command_keeps_package_with_failed_status(search_disabled, transfer):
    models.Transfer.objects.filter(pk=transfer.pk).update(
        status=models.PACKAGE_STATUS_FAILED
    )

    call_command("purge_transient_processing_data", "--keep-failed")

    assert models.Transfer.objects.filter(pk=transfer.pk).count() == 1


@pytest.mark.django_db
def test_purge_command_skips_recent_packages(search_disabled, transfer):
    call_command("purge_transient_processing_data", "--age", "0 00:06:00")

    assert models.Transfer.objects.filter(pk=transfer.pk).count() == 1


@pytest.mark.django_db
def test_purge_command_removes_package_matching_age_criteria(search_disabled, transfer):
    models.Transfer.objects.filter(pk=transfer.pk).update(
        completed_at=timezone.now() - timedelta(1)
    )

    call_command("purge_transient_processing_data", "--age", "0 00:06:00")

    assert models.Transfer.objects.filter(pk=transfer.pk).count() == 0


@pytest.mark.django_db
def test_purge_command_removes_search_documents(search_enabled, transfer, mocker):
    mocker.patch(
        "main.management.commands.purge_transient_processing_data.es.create_indexes_if_needed"
    )
    mock_remove_backlog_transfer = mocker.patch(
        "main.management.commands.purge_transient_processing_data.es.remove_backlog_transfer"
    )
    mock_remove_backlog_transfer_files = mocker.patch(
        "main.management.commands.purge_transient_processing_data.es.remove_backlog_transfer_files"
    )

    call_command("purge_transient_processing_data")

    mock_remove_backlog_transfer.assert_called_once_with(mocker.ANY, str(transfer.pk))
    mock_remove_backlog_transfer_files.assert_called_once_with(
        mocker.ANY, str(transfer.pk)
    )


@pytest.mark.django_db
def test_purge_command_skips_active_packages(search_disabled, transfer, sip, capsys):
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
def test_purge_command_output(search_disabled, transfer, sip, capsys):
    call_command("purge_transient_processing_data")
    captured = capsys.readouterr()

    assert "Transfer %s with status Done" % transfer.pk in captured.out
    assert "SIP %s with status Done" % sip.pk in captured.out
