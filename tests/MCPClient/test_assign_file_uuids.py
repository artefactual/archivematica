import uuid
from unittest import mock

import pytest
from assign_file_uuids import call
from client.job import Job
from main import models


@pytest.fixture
def sip_directory_path(sip_directory_path):
    # Create a directory to test subdirectory filtering.
    contents_dir = sip_directory_path / "contents"
    contents_dir.mkdir()
    (contents_dir / "file-in.txt").touch()

    # Create a file outside the contents directory.
    (sip_directory_path / "file-out.txt").touch()

    # Create a directory to represent a reingest.
    (sip_directory_path / "reingest").mkdir()

    return sip_directory_path


@pytest.mark.django_db
def test_call_creates_transfer_files_and_events(sip_directory_path, transfer):
    job = mock.MagicMock(
        spec=Job,
        args=[
            "assign_file_uuids.py",
            "--transferUUID",
            str(transfer.uuid),
            "--sipDirectory",
            str(sip_directory_path),
            "--filterSubdir",
            "contents",
        ],
    )

    # Verify there are no files or events yet.
    assert models.File.objects.filter(transfer=transfer).count() == 0
    assert models.Event.objects.filter().count() == 0

    call([job])

    # Verify the job succeeded.
    job.set_status.assert_called_once_with(0)

    # Verify a file and an ingestion event were created.
    f = models.File.objects.get(transfer=transfer)
    assert models.Event.objects.filter(file_uuid=f, event_type="ingestion").count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "job_arguments",
    [
        (["assign_file_uuids.py"]),
        (
            [
                "assign_file_uuids.py",
                "--transferUUID",
                str(uuid.uuid4()),
                "--sipUUID",
                str(uuid.uuid4()),
            ]
        ),
    ],
    ids=["no_transfer_nor_sip_provided", "transfer_and_sip_provided"],
)
def test_call_validates_job_arguments(job_arguments):
    job = mock.MagicMock(
        spec=Job,
        args=job_arguments,
    )

    call([job])

    # Verify the job did not succeed.
    job.set_status.assert_called_once_with(2)
    job.print_error.assert_called_once_with(
        "SIP exclusive-or Transfer UUID must be defined"
    )


@pytest.mark.django_db
@mock.patch("metsrw.METSDocument.fromfile")
@mock.patch("assign_file_uuids.find_mets_file")
@mock.patch("assign_file_uuids.get_file_info_from_mets")
def test_call_updates_transfer_file_on_reingest(
    get_file_info_from_mets,
    find_mets_file,
    fromfile,
    sip_directory_path,
    transfer,
):
    # Fake METS parsing and return static file information.

    file_info = {
        "uuid": str(uuid.uuid4()),
        "filegrpuse": "original",
        "original_path": str(sip_directory_path / "contents" / "file-in.txt"),
        "current_path": str(sip_directory_path / "reingest" / "file-in.txt"),
    }
    get_file_info_from_mets.return_value = file_info

    job = mock.MagicMock(
        spec=Job,
        args=[
            "assign_file_uuids.py",
            "--transferUUID",
            str(transfer.uuid),
            "--sipDirectory",
            str(sip_directory_path),
            "--filterSubdir",
            "contents",
        ],
    )

    # Mark the transfer as reingested.
    transfer.type = models.Transfer.ARCHIVEMATICA_AIP
    transfer.save()

    # Verify there are no files or events yet.
    assert models.File.objects.filter(transfer=transfer).count() == 0
    assert models.Event.objects.filter().count() == 0

    call([job])

    # Verify the job succeeded.
    job.set_status.assert_called_once_with(0)

    # Verify a file and a reingestion event were created.
    f = models.File.objects.get(transfer=transfer)
    assert str(f.uuid) == file_info["uuid"]
    assert f.filegrpuse == file_info["filegrpuse"]
    assert (
        models.Event.objects.filter(file_uuid=f, event_type="reingestion").count() == 1
    )

    # Verify the location of the file was updated.
    job.print_output.assert_called_with(
        "Updating current location for", str(f.uuid), "with", file_info
    )
