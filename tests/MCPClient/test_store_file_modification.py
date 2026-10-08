import datetime
import os
import pathlib

import pytest
import pytest_django
from django.utils.timezone import get_current_timezone

from archivematica.dashboard.main import models
from archivematica.MCPClient.clientScripts import store_file_modification_dates


@pytest.mark.django_db
def test_store_file_modification_dates(
    settings: pytest_django.Settings,
    tmp_path: pathlib.Path,
    unicode_transfer: models.Transfer,
    unicode_transfer_files: list[models.File],
) -> None:
    """It should store file modification dates."""
    settings.TIME_ZONE = "US/Eastern"
    shared_path = os.path.join(tmp_path, "")
    transfer_path = unicode_transfer.currentlocation.replace(
        "%sharedPath%", shared_path
    )

    # Create files
    for file_ in unicode_transfer_files:
        path = file_.currentlocation.decode().replace(
            "%transferDirectory%", transfer_path
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(path.encode("utf8"))
        os.utime(path, (1049597970, 1049597970))

    # Store file modification dates
    store_file_modification_dates.main(
        str(unicode_transfer.uuid), shared_path, get_current_timezone()
    )

    # Assert files have expected modification times
    expected_time = datetime.datetime(
        2003, 4, 6, 2, 59, 30, tzinfo=datetime.timezone.utc
    )
    assert list(
        models.File.objects.filter(transfer=unicode_transfer).values_list(
            "modificationtime", flat=True
        )
    ) == [expected_time] * len(unicode_transfer_files)
