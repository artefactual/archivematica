import pathlib
from unittest import mock

import load_labels_from_csv
import pytest
from client.job import Job
from main import models

LABEL = "my file"
OBJECTS_DIRECTORY = "%transferDirectory%objects"


@pytest.fixture()
def transfer():
    return models.Transfer.objects.create()


@pytest.mark.django_db
def test_load_labels_from_csv_fails_if_file_labels_csv_does_not_exist(
    transfer, tmp_path
):
    non_existent_file_labels_csv = tmp_path / "file_labels.csv"
    job = mock.Mock(
        args=[
            "load_labels_from_csv.py",
            str(transfer.uuid),
            str(non_existent_file_labels_csv),
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    load_labels_from_csv.call([job])

    job.pyprint.assert_called_once_with(
        "No such file:", str(non_existent_file_labels_csv)
    )
    job.set_status.assert_called_once_with(0)


@pytest.fixture()
def file(transfer):
    location = f"{OBJECTS_DIRECTORY}/file.txt".encode()

    return models.File.objects.create(
        transfer=transfer, originallocation=location, currentlocation=location
    )


@pytest.fixture()
def file_labels_csv(tmp_path, file):
    result = tmp_path / "file_labels.csv"
    original_file_path = pathlib.Path(file.originallocation.decode()).relative_to(
        OBJECTS_DIRECTORY
    )
    result.write_text(f"{original_file_path},{LABEL}")

    return result


@pytest.mark.django_db
def test_load_labels_from_csv_sets_label_for_files_in_csv(
    transfer, file_labels_csv, file
):
    job = mock.Mock(
        args=["load_labels_from_csv.py", str(transfer.uuid), str(file_labels_csv)],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    load_labels_from_csv.call([job])

    assert (
        models.File.objects.filter(
            transfer=transfer, originallocation=file.originallocation, label=LABEL
        ).count()
        == 1
    )
