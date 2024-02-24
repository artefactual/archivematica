import pytest
from assign_uuids_to_directories import main
from client.job import Job
from main import models


@pytest.fixture
def transfer():
    return models.Transfer.objects.create(
        currentlocation=r"%transferDirectory%",
    )


@pytest.fixture
def transfer_dir(tmp_path):
    transfer_dir = tmp_path / "dir"
    transfer_dir.mkdir()

    # Create a directory with contents.
    contents_dir = transfer_dir / "contents"
    contents_dir.mkdir()
    (contents_dir / "file-in.txt").touch()

    # Create a file outside the contents directory.
    (transfer_dir / "file-out.txt").touch()

    # Create a directory to represent a reingest.
    (transfer_dir / "reingest").mkdir()

    return transfer_dir


@pytest.mark.django_db
def test_main(mocker, transfer, transfer_dir):
    job = mocker.Mock(spec=Job)
    include_dirs = True

    # Verify there are no directories.
    assert models.Directory.objects.count() == 0

    result = main(job, str(transfer_dir), transfer.uuid, include_dirs)

    assert result == 0

    # Verify two directories were created.
    assert models.Directory.objects.filter(transfer=transfer).count() == 2
