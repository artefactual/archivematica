from unittest import mock

import pytest
from assign_uuids_to_directories import main
from client.job import Job
from main import models


@pytest.fixture
def transfer_directory_path(transfer_directory_path):
    # Create a directory with contents.
    contents_dir = transfer_directory_path / "contents"
    contents_dir.mkdir()
    (contents_dir / "file-in.txt").touch()

    # Create a file outside the contents directory.
    (transfer_directory_path / "file-out.txt").touch()

    # Create a directory to represent a reingest.
    (transfer_directory_path / "reingest").mkdir()

    return transfer_directory_path


@pytest.mark.django_db
def test_main(transfer, transfer_directory_path):
    job = mock.Mock(spec=Job)
    include_dirs = True

    # Verify there are no directories.
    assert models.Directory.objects.count() == 0

    result = main(job, str(transfer_directory_path), transfer.uuid, include_dirs)

    assert result == 0

    # Verify two directories were created.
    assert models.Directory.objects.filter(transfer=transfer).count() == 2
