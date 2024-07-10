import pathlib
from unittest import mock

import pytest
import transcribe_file
from client.job import Job
from django.utils import timezone
from fpr import models as fprmodels
from main import models

EXECUTE_OR_RUN_STDOUT = "Hello"


@pytest.fixture(scope="module", autouse=True)
def execute_or_run():
    with mock.patch(
        "transcribe_file.executeOrRun", return_value=(0, EXECUTE_OR_RUN_STDOUT, "")
    ):
        yield


@pytest.fixture
def sip_directory(tmp_path):
    result = tmp_path / "sip"
    result.mkdir()

    return result


@pytest.fixture
def sip(sip_directory):
    return models.SIP.objects.create(currentpath=f"{sip_directory}/")


@pytest.fixture
def file(sip, sip_directory):
    location = b"%SIPDirectory%objects/file.jpg"
    file_dir = sip_directory / "objects"
    file_dir.mkdir(parents=True)
    file_name = pathlib.Path(location.decode()).name
    (file_dir / file_name).touch()

    return models.File.objects.create(
        sip=sip,
        filegrpuse="original",
        currentlocation=location,
        originallocation=location,
    )


@pytest.fixture
def tool():
    return fprmodels.FPTool.objects.create()


@pytest.fixture
def command(tool, file):
    return fprmodels.FPCommand.objects.create(
        tool=tool,
        description="Transcribe using Tesseract",
        command_usage="transcription",
        command="echo Hello",
        script_type="bashScript",
        output_location=file.currentlocation.decode(),
    )


@pytest.fixture
def format_group():
    return fprmodels.FormatGroup.objects.get(description="Image (Raster)")


@pytest.fixture
def format(format_group):
    return fprmodels.Format.objects.create(group=format_group)


@pytest.fixture
def format_version(format):
    return fprmodels.FormatVersion.objects.create(format=format)


@pytest.fixture
def file_format_version(file, format_version):
    return models.FileFormatVersion.objects.create(
        file_uuid=file, format_version=format_version
    )


@pytest.fixture
def fprule(format_version, command):
    return fprmodels.FPRule.objects.create(
        format=format_version, command=command, purpose="transcription"
    )


@pytest.fixture
def preservation_file(sip):
    location = b"%SIPDirectory%objects/preservation/file.tiff"
    return models.File.objects.create(
        sip=sip,
        filegrpuse="preservation",
        currentlocation=location,
        originallocation=location,
    )


@pytest.fixture
def derivation(file, preservation_file):
    return models.Derivation.objects.create(
        source_file=file, derived_file=preservation_file
    )


@pytest.fixture
def preservation_file_format_version(preservation_file, format_version):
    return models.FileFormatVersion.objects.create(
        file_uuid=preservation_file, format_version=format_version
    )


@pytest.fixture
def derivative_file_fprule(format_version, command):
    return fprmodels.FPRule.objects.create(
        format=format_version,
        command=command,
        purpose="transcription",
    )


@pytest.fixture
def job():
    return models.Job.objects.create(createdtime=timezone.now())


@pytest.fixture
def task(job):
    return models.Task.objects.create(job=job, createdtime=timezone.now())


@pytest.mark.django_db
def test_main(file, task, fprule, file_format_version):
    job = mock.Mock(spec=Job)

    result = transcribe_file.main(job, task_uuid=task.taskuuid, file_uuid=file.uuid)

    assert result == 0

    assert job.write_output.mock_calls == [mock.call(EXECUTE_OR_RUN_STDOUT)]
    assert (
        models.Event.objects.filter(
            file_uuid_id=file.uuid,
            event_type="transcription",
            event_outcome="transcribed",
            event_outcome_detail="%SIPDirectory%objects/file.jpg",
        ).count()
        == 1
    )
    assert models.File.objects.count() == 2
    assert (
        models.File.objects.filter(
            filegrpuse="original",
            originallocation=file.originallocation,
            currentlocation=file.currentlocation,
        ).count()
        == 1
    )
    assert (
        models.File.objects.filter(
            filegrpuse="text/ocr",
            originallocation=file.originallocation,
            currentlocation=file.currentlocation,
        ).count()
        == 1
    )
    assert (
        models.Derivation.objects.filter(
            event__event_type="transcription",
            source_file_id=file.uuid,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_main_if_filegroup_is_not_original(
    preservation_file, task, fprule, file_format_version, capsys
):
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
def test_main_if_no_rules_exist(file, task, file_format_version, capsys):
    job = mock.Mock(spec=Job)

    result = transcribe_file.main(job, task_uuid=task.taskuuid, file_uuid=file.uuid)

    assert result == 0

    # No event is stored in the database as there is no transcription on file
    assert models.Event.objects.filter(event_type="transcription").count() == 0
    assert job.print_error.mock_calls == [
        mock.call(
            f"No rules found for file {file.uuid} and its derivatives; not transcribing"
        )
    ]


@pytest.mark.django_db
def test_fetch_rules_for_derivatives_if_rules_are_absent_for_derivates(
    derivation, fprule, file_format_version
):
    result = transcribe_file.fetch_rules_for_derivatives(file_=derivation.source_file)

    assert result == (None, [])


@pytest.mark.django_db
def test_fetch_rules_for_derivatives(
    derivation, derivative_file_fprule, preservation_file_format_version
):
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
