import pathlib
from unittest import mock

import pytest
import pytest_django
import transcribe_file
from client.job import Job
from fpr import models as fprmodels
from main import models

EXECUTE_OR_RUN_STDOUT = "Hello"


@pytest.fixture()
def sip(sip: models.SIP) -> models.SIP:
    # ReplacementDict expands SIP paths based on the shared directory.
    sip.currentpath = "%sharedPath%"
    sip.save()

    return sip


@pytest.fixture
def create_sip_file(sip_directory_path: pathlib.Path, sip_file: models.File) -> None:
    file_path = pathlib.Path(
        sip_file.currentlocation.decode().replace("%SIPDirectory%", "")
    )

    file_dir = sip_directory_path / file_path.parent
    file_dir.mkdir(parents=True)

    (file_dir / file_path.name).touch()


@pytest.fixture
def fpcommand(
    fpcommand: fprmodels.FPCommand, sip_file: models.File
) -> fprmodels.FPCommand:
    fpcommand.output_location = sip_file.currentlocation.decode()
    fpcommand.save()

    return fpcommand


@pytest.fixture
def derivation(
    sip_file: models.File, preservation_file: models.File
) -> models.Derivation:
    return models.Derivation.objects.create(
        source_file=sip_file, derived_file=preservation_file
    )


@pytest.fixture
def preservation_file_format_version(
    preservation_file: models.File, format_version: fprmodels.FormatVersion
) -> models.FileFormatVersion:
    return models.FileFormatVersion.objects.create(
        file_uuid=preservation_file, format_version=format_version
    )


@pytest.mark.django_db
@mock.patch("transcribe_file.executeOrRun", return_value=(0, EXECUTE_OR_RUN_STDOUT, ""))
def test_main(
    execute_or_run: mock.Mock,
    sip_file: models.File,
    task: models.Task,
    fprule_transcription: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
    settings: pytest_django.fixtures.SettingsWrapper,
    sip_directory_path: pathlib.Path,
    create_sip_file: None,
) -> None:
    job = mock.Mock(spec=Job)
    settings.SHARED_DIRECTORY = f"{sip_directory_path}/"

    result = transcribe_file.main(job, task_uuid=task.taskuuid, file_uuid=sip_file.uuid)

    assert result == 0

    assert job.write_output.mock_calls == [mock.call(EXECUTE_OR_RUN_STDOUT)]
    assert (
        models.Event.objects.filter(
            file_uuid_id=sip_file.uuid,
            event_type="transcription",
            event_outcome="transcribed",
            event_outcome_detail=sip_file.currentlocation.decode(),
        ).count()
        == 1
    )
    assert models.File.objects.count() == 2
    assert (
        models.File.objects.filter(
            filegrpuse="original",
            originallocation=sip_file.originallocation,
            currentlocation=sip_file.currentlocation,
        ).count()
        == 1
    )
    assert (
        models.File.objects.filter(
            filegrpuse="text/ocr",
            originallocation=sip_file.currentlocation,
            currentlocation=sip_file.currentlocation,
        ).count()
        == 1
    )
    assert (
        models.Derivation.objects.filter(
            event__event_type="transcription",
            source_file_id=sip_file.uuid,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_main_if_filegroup_is_not_original(
    preservation_file: models.File,
    task: models.Task,
    fprule_transcription: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
    capsys: pytest.CaptureFixture[str],
) -> None:
    job = mock.Mock(spec=Job)

    result = transcribe_file.main(
        job, task_uuid=task.taskuuid, file_uuid=preservation_file.uuid
    )

    assert result == 0

    # No event is stored in the database as there is no transcription on file
    assert models.Event.objects.filter(event_type="transcription").count() == 0
    assert job.print_error.mock_calls == [
        mock.call(f"{preservation_file.uuid} is not an original; not transcribing")
    ]


@pytest.mark.django_db
def test_main_if_no_rules_exist(
    sip_file: models.File,
    task: models.Task,
    sip_file_format_version: models.FileFormatVersion,
    capsys: pytest.CaptureFixture[str],
) -> None:
    job = mock.Mock(spec=Job)

    result = transcribe_file.main(job, task_uuid=task.taskuuid, file_uuid=sip_file.uuid)

    assert result == 0

    # No event is stored in the database as there is no transcription on file
    assert models.Event.objects.filter(event_type="transcription").count() == 0
    assert job.print_error.mock_calls == [
        mock.call(
            f"No rules found for file {sip_file.uuid} and its derivatives; not transcribing"
        )
    ]


@pytest.mark.django_db
def test_fetch_rules_for_derivatives_if_rules_are_absent_for_derivates(
    derivation: models.Derivation,
    fprule_transcription: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
) -> None:
    result = transcribe_file.fetch_rules_for_derivatives(file_=derivation.source_file)

    assert result == (None, [])


@pytest.mark.django_db
def test_fetch_rules_for_derivatives(
    derivation: models.Derivation,
    fprule_transcription: fprmodels.FPRule,
    preservation_file_format_version: models.FileFormatVersion,
) -> None:
    derived_file, rules_of_derived_file = transcribe_file.fetch_rules_for_derivatives(
        file_=derivation.source_file
    )

    assert list(rules_of_derived_file.values_list("purpose")) == [("transcription",)]

    assert (
        models.Derivation.objects.filter(
            derived_file__filegrpuse="preservation",
            derived_file_id=derived_file.uuid,
            source_file_id=derivation.source_file.uuid,
        ).count()
        == 1
    )


@pytest.fixture
def disabled_fprule_transcription(
    fprule_transcription: fprmodels.FPRule,
) -> fprmodels.FPRule:
    fprule_transcription.enabled = 0
    fprule_transcription.save()

    return fprule_transcription


@pytest.mark.django_db
def test_main_if_fprule_is_disabled(
    sip_file: models.File,
    task: models.Task,
    disabled_fprule_transcription: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
) -> None:
    job = mock.Mock(spec=Job)

    result = transcribe_file.main(job, task_uuid=task.taskuuid, file_uuid=sip_file.uuid)

    assert result == 0

    assert job.write_output.mock_calls == []
    assert (
        models.Event.objects.filter(
            file_uuid_id=sip_file.uuid,
            event_type="transcription",
            event_outcome="transcribed",
            event_outcome_detail=sip_file.currentlocation.decode(),
        ).count()
        == 0
    )
    assert (
        models.File.objects.filter(
            filegrpuse="original",
            originallocation=sip_file.originallocation,
            currentlocation=sip_file.currentlocation,
        ).count()
        == 1
    )
    assert (
        models.File.objects.filter(
            filegrpuse="text/ocr",
            originallocation=sip_file.originallocation,
            currentlocation=sip_file.currentlocation,
        ).count()
        == 0
    )
    assert (
        models.Derivation.objects.filter(
            event__event_type="transcription",
            source_file_id=sip_file.uuid,
        ).count()
        == 0
    )


@pytest.mark.django_db
@mock.patch("transcribe_file.executeOrRun")
def test_main_if_command_is_not_bash_script(
    execute_or_run: mock.Mock,
    fpcommand: fprmodels.FPCommand,
    sip_file: models.File,
    task: models.Task,
    fprule_transcription: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
) -> None:
    execute_or_run.return_value = (0, fpcommand.command, "")
    job = mock.Mock(spec=Job)

    result = transcribe_file.main(job, task_uuid=task.taskuuid, file_uuid=sip_file.uuid)

    assert result == 0

    assert job.print_error.mock_calls == [
        mock.call(f"Transcribing original {sip_file.uuid}")
    ]
    assert job.write_output.mock_calls == [mock.call(fpcommand.command)]

    # executeOrRun is called once.
    execute_or_run.assert_called_once()

    # Get the call to executeOrRun.
    execute_or_run_call = execute_or_run.mock_calls[0]
    call_kwargs = execute_or_run_call[-1]

    # Ensure the arguments passed is a list.
    execute_or_run_args = call_kwargs["arguments"]
    assert isinstance(execute_or_run_args, list)
