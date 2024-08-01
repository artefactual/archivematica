import pathlib
from unittest import mock

import load_labels_from_csv
import pytest
from client.job import Job
from main import models

LABEL = "my file"
OBJECTS_DIRECTORY = "%transferDirectory%objects"


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
def file_labels_csv(tmp_path, transfer_file):
    result = tmp_path / "file_labels.csv"
    original_file_path = pathlib.Path(
        transfer_file.originallocation.decode()
    ).relative_to(OBJECTS_DIRECTORY)
    result.write_text(f"{original_file_path},{LABEL}")

    return result


@pytest.mark.django_db
def test_load_labels_from_csv_sets_label_for_files_in_csv(
    transfer, file_labels_csv, transfer_file
):
    job = mock.Mock(
        args=["load_labels_from_csv.py", str(transfer.uuid), str(file_labels_csv)],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    load_labels_from_csv.call([job])

    assert (
        models.File.objects.filter(
            transfer=transfer,
            originallocation=transfer_file.originallocation,
            label=LABEL,
        ).count()
        == 1
    )
