import pytest
from django.utils import timezone

from archivematica.dashboard.main import models


@pytest.fixture
def transfer(transfer: models.Transfer) -> models.Transfer:
    """The transfer once its processing is done, with a job and a file."""
    transfer.status = models.PACKAGE_STATUS_DONE
    transfer.completed_at = timezone.now()
    transfer.save()

    models.Job.objects.create(
        sipuuid=transfer.pk, unittype="unitTransfer", createdtime=timezone.now()
    )
    models.File.objects.create(transfer=transfer)

    return transfer


@pytest.fixture
def sip(sip: models.SIP) -> models.SIP:
    """The SIP once its ingest is done, with a job, a file and an access record."""
    sip.status = models.PACKAGE_STATUS_DONE
    sip.completed_at = timezone.now()
    sip.save()

    models.Job.objects.create(
        sipuuid=sip.pk, unittype="unitSIP", createdtime=timezone.now()
    )
    models.File.objects.create(sip=sip)
    models.Access.objects.create(sipuuid=sip.pk)

    return sip
