import pytest
from django.db.models import Q
from fileOperations import addAccessionEvent
from fileOperations import get_extract_dir_name
from main.models import Event
from main.models import File
from main.models import Transfer


@pytest.mark.parametrize(
    "filename,dirname",
    [
        ("/parent/test.zip", "/parent/test"),
        ("/parent/test.tar.gz", "/parent/test"),
        ("/parent/test.TAR.GZ", "/parent/test"),
        ("/parent/test.TAR.GZ", "/parent/test"),
        (
            "/parent/test.target.tar.gz",
            "/parent/test.target",
        ),  # something beginning with "tar"
    ],
)
def test_get_extract_dir_name(filename, dirname):
    assert get_extract_dir_name(filename) == dirname


def test_get_extract_dir_name_raises_if_no_extension():
    with pytest.raises(ValueError):
        get_extract_dir_name("test")


@pytest.mark.django_db
def test_addAccessionEvent_adds_registration_event_when_accessionid_is_set():
    f = File.objects.create()
    t = Transfer.objects.create(accessionid="my-id")
    date = None
    query_filter = Q(
        file_uuid=f,
        event_type="registration",
        event_outcome_detail="accession#my-id",
    )

    assert Event.objects.filter(query_filter).count() == 0

    addAccessionEvent(f.uuid, t.uuid, date)

    assert Event.objects.filter(query_filter).count() == 1
