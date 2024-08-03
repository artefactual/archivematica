import pathlib
from unittest import mock

import extract_contents
import pytest
from client.job import Job
from main import models


@pytest.mark.django_db
def test_job_fails_if_transfer_contains_no_files(
    transfer, transfer_directory_path, task
):
    date = "2024-08-01"
    delete = str(False)
    job = mock.Mock(
        args=[
            "extract_contents",
            str(transfer.uuid),
            f"{transfer_directory_path}/",
            date,
            str(task.taskuuid),
            delete,
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    extract_contents.call([job])
    job.set_status.assert_called_once_with(255)

    assert job.pyprint.mock_calls == [
        mock.call(f"Deleting?: {delete}", file=mock.ANY),
        mock.call("No files found for transfer: ", str(transfer.uuid)),
    ]


@pytest.mark.django_db
def test_job_fails_if_transfer_file_format_was_not_identified(
    transfer, transfer_directory_path, task, transfer_file
):
    date = "2024-08-01"
    delete = str(False)
    job = mock.Mock(
        args=[
            "extract_contents",
            str(transfer.uuid),
            f"{transfer_directory_path}/",
            date,
            str(task.taskuuid),
            delete,
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    extract_contents.call([job])
    job.set_status.assert_called_once_with(255)

    assert job.pyprint.mock_calls == [
        mock.call(f"Deleting?: {delete}", file=mock.ANY),
        mock.call(
            "Not extracting contents from",
            pathlib.Path(transfer_file.currentlocation.decode()).name,
            " - file format not identified",
            file=mock.ANY,
        ),
    ]


@pytest.mark.django_db
def test_job_fails_if_extraction_command_does_not_exist(
    transfer,
    transfer_directory_path,
    task,
    transfer_file,
    transfer_file_format_version,
    fpcommand,
):
    date = "2024-08-01"
    delete = str(False)
    job = mock.Mock(
        args=[
            "extract_contents",
            str(transfer.uuid),
            f"{transfer_directory_path}/",
            date,
            str(task.taskuuid),
            delete,
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    extract_contents.call([job])
    job.set_status.assert_called_once_with(255)

    assert job.pyprint.mock_calls == [
        mock.call(f"Deleting?: {delete}", file=mock.ANY),
        mock.call(
            "Not extracting contents from",
            pathlib.Path(transfer_file.currentlocation.decode()).name,
            " - No rule found to extract",
            file=mock.ANY,
        ),
    ]


@pytest.fixture
def unpacked_file(transfer, transfer_file):
    location = f"{transfer_file.currentlocation.decode()}/unpacked".encode()
    return models.File.objects.create(
        transfer=transfer, originallocation=location, currentlocation=location
    )


@pytest.fixture
def unpacking_event(unpacked_file):
    return models.Event.objects.create(
        file_uuid=unpacked_file,
        event_type="unpacking",
        event_detail=unpacked_file.currentlocation.decode(),
    )


@pytest.mark.django_db
def test_job_fails_if_file_has_been_extracted_already(
    transfer,
    transfer_directory_path,
    task,
    transfer_file,
    transfer_file_format_version,
    fprule_extraction,
    unpacked_file,
    unpacking_event,
):
    date = "2024-08-01"
    delete = str(False)
    job = mock.Mock(
        args=[
            "extract_contents",
            str(transfer.uuid),
            f"{transfer_directory_path}/",
            date,
            str(task.taskuuid),
            delete,
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    extract_contents.call([job])
    job.set_status.assert_called_once_with(255)

    expected_pyprint_calls = [
        mock.call(f"Deleting?: {delete}", file=mock.ANY),
        mock.call(
            "Not extracting contents from",
            pathlib.Path(transfer_file.currentlocation.decode()).name,
            " - extraction already happened.",
            file=mock.ANY,
        ),
        mock.call(
            "Not extracting contents from",
            pathlib.Path(unpacked_file.currentlocation.decode()).name,
            " - file format not identified",
            file=mock.ANY,
        ),
    ]
    assert len(job.pyprint.mock_calls) == len(expected_pyprint_calls)
    # This uses any_order because we do not control the order in which the
    # jo iterates the files in the transfer.
    job.pyprint.assert_has_calls(expected_pyprint_calls, any_order=True)


@pytest.fixture
def transfer_file_path(transfer_directory_path, transfer_file):
    transfer_file_relative_path = pathlib.Path(
        transfer_file.currentlocation.decode().replace(
            extract_contents.TRANSFER_DIRECTORY, ""
        )
    )
    result = transfer_directory_path / transfer_file_relative_path
    (result.parent).mkdir(parents=True)
    result.touch()

    return result


@pytest.mark.django_db
@mock.patch("extract_contents.executeOrRun", return_value=(-1, "", "error!"))
def test_job_fails_if_extraction_command_fails(
    execute_or_run,
    transfer,
    transfer_directory_path,
    task,
    transfer_file,
    transfer_file_format_version,
    fpcommand,
    fprule_extraction,
    caplog,
    transfer_file_path,
):
    date = "2024-08-01"
    delete = str(False)
    job = mock.Mock(
        args=[
            "extract_contents",
            str(transfer.uuid),
            f"{transfer_directory_path}/",
            date,
            str(task.taskuuid),
            delete,
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    extract_contents.call([job])
    job.set_status.assert_called_once_with(255)

    execute_or_run.assert_called_once_with(
        fpcommand.script_type,
        fpcommand.command,
        arguments=[f"{transfer_file_path}", f"{transfer_file_path}-{date}"],
        printing=True,
        capture_output=True,
    )

    assert [r.message for r in caplog.records] == [
        f"Command to execute is: {fpcommand.command}"
    ]
    assert job.pyprint.mock_calls == [
        mock.call(f"Deleting?: {delete}", file=mock.ANY),
        mock.call("Command", fpcommand.description, "failed!", file=mock.ANY),
    ]


@pytest.mark.django_db
@mock.patch("extract_contents.executeOrRun", return_value=(0, "success!", ""))
def test_job_deletes_compressed_file(
    execute_or_run,
    transfer,
    transfer_directory_path,
    task,
    transfer_file,
    transfer_file_format_version,
    fpcommand,
    fprule_extraction,
    caplog,
    transfer_file_path,
):
    date = "2024-08-01"
    delete = str(True)
    job = mock.Mock(
        args=[
            "extract_contents",
            str(transfer.uuid),
            f"{transfer_directory_path}/",
            date,
            str(task.taskuuid),
            delete,
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    extract_contents.call([job])
    job.set_status.assert_called_once_with(0)

    execute_or_run.assert_called_once_with(
        fpcommand.script_type,
        fpcommand.command,
        arguments=[f"{transfer_file_path}", f"{transfer_file_path}-{date}"],
        printing=True,
        capture_output=True,
    )

    # The compressed file was deleted.
    assert not transfer_file_path.exists()
    assert (
        models.Event.objects.filter(
            file_uuid=transfer_file,
            event_type="file removed",
            event_detail=f"removed from: {transfer_file.currentlocation.decode()}",
        ).count()
        == 1
    )

    assert [r.message for r in caplog.records] == [
        f"Command to execute is: {fpcommand.command}"
    ]
    assert job.pyprint.mock_calls == [
        mock.call(f"Deleting?: {delete}", file=mock.ANY),
        mock.call(
            "Extracted contents from",
            pathlib.Path(transfer_file.currentlocation.decode()).name,
        ),
        mock.call(f"Package removed: {transfer_file_path}"),
    ]


@pytest.mark.django_db
@mock.patch("extract_contents.executeOrRun")
def test_job_assign_uuids_to_extracted_files_and_directories(
    execute_or_run,
    transfer,
    transfer_directory_path,
    task,
    transfer_file,
    transfer_file_format_version,
    fpcommand,
    fprule_extraction,
    caplog,
    transfer_file_path,
    unpacked_file,
):
    unpacked_file_relative_path = pathlib.Path(unpacked_file.currentlocation.decode())

    def execute_or_run_side_effect(*args, **kwargs):
        """Mock extraction by creating a new temporary file."""
        compressed_file_path, extraction_tmp_path = (
            pathlib.Path(p) for p in kwargs["arguments"]
        )
        assert compressed_file_path == transfer_file_path

        extraction_tmp_path.mkdir()
        (extraction_tmp_path / unpacked_file_relative_path.name).touch()

        return (0, "success!", "")

    execute_or_run.side_effect = execute_or_run_side_effect

    date = "2024-08-01"
    delete = str(False)
    job = mock.Mock(
        args=[
            "extract_contents",
            str(transfer.uuid),
            f"{transfer_directory_path}/",
            date,
            str(task.taskuuid),
            delete,
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    extract_contents.call([job])
    job.set_status.assert_called_once_with(0)

    execute_or_run.assert_called_once_with(
        fpcommand.script_type,
        fpcommand.command,
        arguments=[f"{transfer_file_path}", f"{transfer_file_path}-{date}"],
        printing=True,
        capture_output=True,
    )

    # The new extracted file was created in the database.
    extracted_file = models.File.objects.get(
        originallocation=unpacked_file.originallocation,
        currentlocation=f"{transfer_file.currentlocation.decode()}-{date}/{unpacked_file_relative_path.name}".encode(),
    )

    # PREMIS events for unpacking and checksum calculation were created for
    # the new extracted file.
    assert set(
        models.Event.objects.filter(
            file_uuid=extracted_file,
        ).values_list("event_type", "event_detail", "event_outcome_detail")
    ) == {
        (
            "unpacking",
            f"Unpacked from: {transfer_file.currentlocation.decode()} ({transfer_file.uuid})",
            "",
        ),
        (
            "message digest calculation",
            'program="python"; module="hashlib.sha256()"',
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
    }

    # A directory was created to contain the new extracted file.
    extracted_directory = models.Directory.objects.get(
        transfer=transfer,
        originallocation=f"{pathlib.Path(extracted_file.originallocation.decode()).parent}/".encode(),
        currentlocation=f"{pathlib.Path(extracted_file.currentlocation.decode()).parent}/".encode(),
    )

    assert [r.message for r in caplog.records] == [
        f"Command to execute is: {fpcommand.command}",
        f"Assigning UUID {extracted_directory.uuid} to directory path {extracted_directory.currentlocation.decode()}",
    ]
    assert job.pyprint.mock_calls == [
        mock.call(f"Deleting?: {delete}", file=mock.ANY),
        mock.call(
            "Extracted contents from",
            pathlib.Path(transfer_file.currentlocation.decode()).name,
        ),
        mock.call(
            "Assigning new file UUID:",
            str(extracted_file.uuid),
            "to file",
            f"{transfer_file_path}-{date}/{unpacked_file_relative_path.name}",
        ),
        mock.call(
            f"Assigning UUID {extracted_directory.uuid} to directory path {extracted_directory.currentlocation.decode()}",
        ),
        mock.call(
            "Not extracting contents from",
            unpacked_file_relative_path.name,
            " - file format not identified",
            file=mock.ANY,
        ),
    ]


@pytest.mark.django_db
@mock.patch("extract_contents.executeOrRun", return_value=(0, "success", ""))
def test_job_uses_replacement_keys_in_bash_command(
    execute_or_run,
    transfer,
    transfer_directory_path,
    task,
    transfer_file,
    transfer_file_format_version,
    fpcommand,
    fprule_extraction,
    caplog,
    transfer_file_path,
    unpacked_file,
):
    # Set a bash script command that uses the replacement keys.
    fpcommand.script_type = "bashScript"
    fpcommand.command = r"input: %inputFile%, output: %outputDirectory%"
    fpcommand.save()

    date = "2024-08-01"
    delete = str(False)
    job = mock.Mock(
        args=[
            "extract_contents",
            str(transfer.uuid),
            f"{transfer_directory_path}/",
            date,
            str(task.taskuuid),
            delete,
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    extract_contents.call([job])
    job.set_status.assert_called_once_with(0)

    # The keys were replaced in the command to execute.
    execute_or_run.assert_called_once_with(
        fpcommand.script_type,
        f"input: {transfer_file_path}, output: {transfer_file_path}-{date}",
        arguments=[],
        printing=True,
        capture_output=True,
    )
