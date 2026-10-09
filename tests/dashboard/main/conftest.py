import pytest
from django.utils import timezone

from archivematica.dashboard.main import models
from tests.factories import FileFactory
from tests.factories import JobFactory


@pytest.fixture
def transfer(
    make_job: JobFactory, make_file: FileFactory, transfer: models.Transfer
) -> models.Transfer:
    """The transfer once its processing is done, with a job and a file."""
    transfer.status = models.PACKAGE_STATUS_DONE
    transfer.completed_at = timezone.now()
    transfer.save()

    make_job(transfer)
    make_file("objects/file.txt", transfer=transfer)

    return transfer


@pytest.fixture
def sip(make_job: JobFactory, make_file: FileFactory, sip: models.SIP) -> models.SIP:
    """The SIP once its ingest is done, with a job, a file and an access record."""
    sip.status = models.PACKAGE_STATUS_DONE
    sip.completed_at = timezone.now()
    sip.save()

    make_job(sip)
    make_file("objects/file.txt", sip=sip)
    models.Access.objects.create(sipuuid=sip.pk)

    return sip
