from unittest import mock

import check_for_access_directory
import pytest
from client.job import Job
from django.utils import timezone
from main.models import Event
from main.models import File


@pytest.mark.django_db
def test_main(tmp_path, sip, sip_directory_path):
    job = mock.Mock(spec=Job)
    date = timezone.now()

    access_directory = tmp_path / "access"
    access_directory.mkdir()
    (access_directory / "file1.txt").touch()
    (access_directory / "file2.txt").touch()

    objects_directory = tmp_path / "objects"
    objects_directory.mkdir()
    (objects_directory / "file1.txt").touch()
    (objects_directory / "file2.txt").touch()
    (objects_directory / "file3.txt").touch()

    dip_directory = tmp_path / "dip"
    dip_directory.mkdir()
    (dip_directory / "objects").mkdir()

    # Add access files to the database.
    File.objects.create(
        sip=sip,
        originallocation=(access_directory / "file1.txt").as_posix().encode(),
        currentlocation=(access_directory / "file1.txt").as_posix().encode(),
    )
    File.objects.create(
        sip=sip,
        originallocation=(access_directory / "file2.txt").as_posix().encode(),
        currentlocation=(access_directory / "file2.txt").as_posix().encode(),
    )
    assert (
        File.objects.filter(
            sip=sip,
            currentlocation__startswith=access_directory.as_posix(),
        ).count()
        == 2
    )

    # Add objects files to the database.
    File.objects.create(
        sip=sip,
        originallocation=(objects_directory / "file1.txt").as_posix().encode(),
        currentlocation=(objects_directory / "file1.txt").as_posix().encode(),
    )
    File.objects.create(
        sip=sip,
        originallocation=(objects_directory / "file2.txt").as_posix().encode(),
        currentlocation=(objects_directory / "file2.txt").as_posix().encode(),
    )
    File.objects.create(
        sip=sip,
        originallocation=(objects_directory / "file3.txt").as_posix().encode(),
        currentlocation=(objects_directory / "file3.txt").as_posix().encode(),
    )

    # The DIP objects directory is initially empty.
    assert (
        File.objects.filter(
            sip=sip,
            currentlocation__startswith=(dip_directory / "objects").as_posix(),
        ).count()
        == 0
    )

    # And there are no PREMIS "movement" events.
    assert Event.objects.filter(event_type="movement").count() == 0

    result = check_for_access_directory.main(
        job,
        sip_directory_path.as_posix(),
        access_directory.as_posix(),
        objects_directory.as_posix(),
        dip_directory.as_posix(),
        str(sip.uuid),
        date,
    )

    # Files have been moved from the access directory to the DIP objects directory.
    assert (
        File.objects.filter(
            sip=sip,
            currentlocation__startswith=access_directory.as_posix(),
        ).count()
        == 0
    )
    assert (
        File.objects.filter(
            sip=sip,
            currentlocation__startswith=(dip_directory / "objects").as_posix(),
            currentlocation__endswith=".txt",
        ).count()
        == 2
    )

    # And PREMIS "movement" events are created accordingly.
    assert (
        Event.objects.filter(
            event_type="movement",
            event_outcome_detail__startswith=f'moved from="{access_directory.as_posix()}',
            event_outcome_detail__contains=f'moved to="{(dip_directory / "objects").as_posix()}',
            event_datetime__date=date,
        ).count()
        == 2
    )

    assert result == 179
