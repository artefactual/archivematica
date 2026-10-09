import uuid

import pytest

from archivematica.dashboard.fpr.models import IDCommand
from archivematica.dashboard.fpr.utils import get_revision_descendants


@pytest.mark.django_db
def test_get_revision_descendants_appends_replacing_revisions() -> None:
    cmd1 = IDCommand.objects.create()
    cmd2 = IDCommand(description="Foobar")
    cmd2.save(replacing=cmd1)

    assert get_revision_descendants(IDCommand, cmd1.uuid, [123]) == [123, cmd2]


@pytest.mark.django_db
def test_get_revision_descendants_fails_for_unknown_revision() -> None:
    with pytest.raises(IDCommand.DoesNotExist):
        get_revision_descendants(IDCommand, uuid.uuid4(), [])
