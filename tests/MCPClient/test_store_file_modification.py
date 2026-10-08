import datetime
import os
import pathlib

import pytest
import pytest_django
from django.core.management import call_command
from django.utils.timezone import get_current_timezone

from archivematica.dashboard.main import models
from archivematica.MCPClient.clientScripts import store_file_modification_dates

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(THIS_DIR, "fixtures")

# UUID of the transfer created by the transfer.json fixture.
TRANSFER_UUID = "e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6"


@pytest.fixture
def unicode_transfer_fixtures(db: None) -> None:
    call_command(
        "loaddata",
        os.path.join(FIXTURES_DIR, "transfer.json"),
        os.path.join(FIXTURES_DIR, "files-transfer-unicode.json"),
        verbosity=0,
    )


@pytest.mark.django_db
def test_store_file_modification_dates(
    settings: pytest_django.Settings,
    tmp_path: pathlib.Path,
    unicode_transfer_fixtures: None,
) -> None:
    """It should store file modification dates."""
    settings.TIME_ZONE = "US/Eastern"
    shared_path = os.path.join(tmp_path, "")
    transfer = models.Transfer.objects.get(uuid=TRANSFER_UUID)
    transfer_path = transfer.currentlocation.replace("%sharedPath%", shared_path)

    # Create files
    for file_ in models.File.objects.filter(transfer=transfer):
        path = file_.currentlocation.decode().replace(
            "%transferDirectory%", transfer_path
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(path.encode("utf8"))
        os.utime(path, (1049597970, 1049597970))

    # Store file modification dates
    store_file_modification_dates.main(
        TRANSFER_UUID, shared_path, get_current_timezone()
    )

    # Assert files have expected modification times
    expected_time = datetime.datetime(
        2003, 4, 6, 2, 59, 30, tzinfo=datetime.timezone.utc
    )
    assert (
        list(
            models.File.objects.filter(transfer=transfer).values_list(
                "modificationtime", flat=True
            )
        )
        == [expected_time] * 4
    )
