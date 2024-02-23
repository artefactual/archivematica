import uuid

import pytest
from assign_file_uuids import call
from client.job import Job
from main import models


@pytest.fixture
def transfer():
    return models.Transfer.objects.create(
        currentlocation=r"%transferDirectory%",
    )


@pytest.fixture
def sip_dir(tmp_path):
    sip_dir = tmp_path / "dir"
    sip_dir.mkdir()

    # Create a directory to test subdirectory filtering.
    contents_dir = sip_dir / "contents"
    contents_dir.mkdir()
    (contents_dir / "file-in.txt").touch()

    # Create a file outside the contents directory.
    (sip_dir / "file-out.txt").touch()

    # Create a directory to represent a reingest.
    (sip_dir / "reingest").mkdir()

    return sip_dir


@pytest.mark.django_db
def test_call_creates_transfer_files_and_events(mocker, sip_dir, transfer):
    job = mocker.MagicMock(
        spec=Job,
        args=[
            "assign_file_uuids.py",
            "--transferUUID",
            str(transfer.uuid),
            "--sipDirectory",
            str(sip_dir),
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
def test_call_validates_job_arguments(mocker, job_arguments):
    job = mocker.MagicMock(
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
def test_call_updates_transfer_file_on_reingest(mocker, sip_dir, transfer):
    # Fake METS parsing and return static file information.
    mocker.patch("metsrw.METSDocument.fromfile")
    mocker.patch("assign_file_uuids.find_mets_file")
    file_info = {
        "uuid": str(uuid.uuid4()),
        "filegrpuse": "original",
        "original_path": str(sip_dir / "contents" / "file-in.txt"),
        "current_path": str(sip_dir / "reingest" / "file-in.txt"),
    }
    mocker.patch("assign_file_uuids.get_file_info_from_mets", return_value=file_info)

    job = mocker.MagicMock(
        spec=Job,
        args=[
            "assign_file_uuids.py",
            "--transferUUID",
            str(transfer.uuid),
            "--sipDirectory",
            str(sip_dir),
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
