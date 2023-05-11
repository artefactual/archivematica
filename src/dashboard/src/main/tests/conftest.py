import uuid

import pytest
from django.utils import timezone
from main import models


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
