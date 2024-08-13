import pathlib
from unittest import mock

import identify_file_format
import pytest
from client.job import Job
from fpr import models as fprmodels
from main import models


@pytest.fixture
def sip_file_path(
    sip_directory_path: pathlib.Path, sip_file: models.File
) -> pathlib.Path:
    result = sip_directory_path / pathlib.Path(
        sip_file.currentlocation.decode().replace("%SIPDirectory%", "")
    )
    result.parent.mkdir(parents=True)
    result.touch()

    return result


@pytest.fixture
def job(sip_file: models.File, sip_file_path: pathlib.Path) -> mock.Mock:
    return mock.Mock(
        args=[
            "identify_file_format.py",
            "True",
            str(sip_file_path),
            str(sip_file.uuid),
            "--disable-reidentify",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )


@pytest.mark.django_db
def test_job_skips_format_identification_explicitly(job: mock.Mock) -> None:
    job.args[1] = "False"

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.SUCCESS)
    job.print_output.assert_called_once_with("Skipping file format identification")


@pytest.mark.django_db
def test_job_skips_format_identification_if_file_has_format_identification_events(
    job: mock.Mock,
    sip_file: models.File,
    sip_file_path: pathlib.Path,
    idcommand: fprmodels.IDCommand,
) -> None:
    models.Event.objects.create(file_uuid=sip_file, event_type="format identification")

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.SUCCESS)
    assert job.print_output.mock_calls == [
        mock.call("IDCommand:", idcommand.description),
        mock.call("IDCommand UUID:", idcommand.uuid),
        mock.call("IDTool:", idcommand.tool.description),
        mock.call("IDTool UUID:", idcommand.tool.uuid),
        mock.call(f"File: ({sip_file.uuid}) {sip_file_path}"),
        mock.call(
            "This file has already been identified, and re-identification is disabled. Skipping."
        ),
    ]


@pytest.mark.django_db
def test_job_fails_if_identification_command_does_not_exist(job: mock.Mock) -> None:
    fprmodels.IDCommand.objects.all().delete()

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.ERROR)
    job.write_error.assert_called_once_with("Unable to determine IDCommand.\n")


@pytest.mark.django_db
@mock.patch("identify_file_format.executeOrRun")
def test_job_fails_if_format_identification_command_fails(
    execute_or_run: mock.Mock,
    job: mock.Mock,
    idcommand: fprmodels.IDCommand,
) -> None:
    command_error = "error!"
    execute_or_run.return_value = (1, "", command_error)

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.ERROR)
    assert job.print_error.mock_calls == [
        mock.call(f"Error: IDCommand with UUID {idcommand.uuid} exited non-zero."),
        mock.call(f"Error: {command_error}"),
    ]


@pytest.mark.django_db
@mock.patch("identify_file_format.executeOrRun")
def test_job_fails_if_identification_rule_does_not_exist(
    execute_or_run: mock.Mock,
    job: mock.Mock,
    sip_file: models.File,
    idcommand: fprmodels.IDCommand,
) -> None:
    command_output = ".mp3"
    execute_or_run.return_value = (0, command_output, "")

    idcommand.config = ""
    idcommand.save()

    fprmodels.IDRule.objects.filter(command_output=command_output).delete()

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.ERROR)
    assert (
        models.Event.objects.filter(
            file_uuid=sip_file.uuid,
            event_type="format identification",
            event_detail=f'program="{idcommand.tool.description}"; version="{idcommand.tool.version}"',
            event_outcome="Not identified",
            event_outcome_detail="No Matching Format",
        ).count()
        == 1
    )
    job.print_error.assert_called_once_with(
        f'Error: No FPR identification rule for tool output "{command_output}" found'
    )


@pytest.mark.django_db
@mock.patch("identify_file_format.executeOrRun")
def test_job_fails_if_multiple_identification_rules_exist(
    execute_or_run: mock.Mock,
    job: mock.Mock,
    sip_file: models.File,
    idcommand: fprmodels.IDCommand,
    idrule: fprmodels.IDRule,
    format_version: fprmodels.Format,
) -> None:
    command_output = ".mp3"
    execute_or_run.return_value = (0, command_output, "")

    idcommand.config = ""
    idcommand.save()

    fprmodels.IDRule.objects.filter(command_output=command_output).delete()
    fprmodels.IDRule.objects.create(
        command=idcommand, format=format_version, command_output=command_output
    )
    idrule.command_output = command_output
    idrule.save()

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.ERROR)
    assert (
        models.Event.objects.filter(
            file_uuid=sip_file.uuid,
            event_type="format identification",
            event_detail=f'program="{idcommand.tool.description}"; version="{idcommand.tool.version}"',
            event_outcome="Not identified",
            event_outcome_detail="No Matching Format",
        ).count()
        == 1
    )
    job.print_error.assert_called_once_with(
        f'Error: Multiple FPR identification rules for tool output "{command_output}" found'
    )


@pytest.mark.django_db
@mock.patch("identify_file_format.executeOrRun")
def test_job_fails_if_format_version_does_not_exist(
    execute_or_run: mock.Mock,
    job: mock.Mock,
    sip_file: models.File,
    idcommand: fprmodels.IDCommand,
) -> None:
    command_output = ".mp3"
    execute_or_run.return_value = (0, command_output, "")

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.ERROR)
    assert (
        models.Event.objects.filter(
            file_uuid=sip_file.uuid,
            event_type="format identification",
            event_detail=f'program="{idcommand.tool.description}"; version="{idcommand.tool.version}"',
            event_outcome="Not identified",
            event_outcome_detail="No Matching Format",
        ).count()
        == 1
    )
    job.print_error.assert_called_once_with(
        f"Error: No FPR format record found for PUID {command_output}"
    )


@pytest.mark.django_db
@mock.patch("identify_file_format.executeOrRun", return_value=(0, "success!", ""))
def test_job_saves_unit_variable_indicating_file_format_identification_use(
    execute_or_run: mock.Mock,
    job: mock.Mock,
    sip: models.SIP,
) -> None:
    identify_file_format.call([job])

    assert (
        models.UnitVariable.objects.filter(
            unituuid=sip.pk,
            variable="replacementDict",
            variablevalue="{'%IDCommand%': 'True'}",
        ).count()
        == 1
    )


@pytest.mark.django_db
@mock.patch("identify_file_format.executeOrRun")
def test_job_adds_file_format_version(
    execute_or_run: mock.Mock,
    job: mock.Mock,
    sip_file: models.File,
    sip_file_path: pathlib.Path,
    idcommand: fprmodels.IDCommand,
    format_version: fprmodels.FormatVersion,
) -> None:
    command_output = "fmt/111"
    execute_or_run.return_value = (0, command_output, "")

    fprmodels.FormatVersion.objects.filter(pronom_id=command_output).delete()
    format_version.pronom_id = command_output
    format_version.save()

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.SUCCESS)
    assert (
        models.FileFormatVersion.objects.filter(
            file_uuid=sip_file, format_version=format_version
        ).count()
        == 1
    )
    assert job.print_output.mock_calls == [
        mock.call("IDCommand:", idcommand.description),
        mock.call("IDCommand UUID:", idcommand.uuid),
        mock.call("IDTool:", idcommand.tool.description),
        mock.call("IDTool UUID:", idcommand.tool.uuid),
        mock.call(f"File: ({sip_file.uuid}) {sip_file_path}"),
        mock.call("Command output:", command_output),
        mock.call(f"{sip_file_path} identified as a {format_version.description}"),
    ]


@pytest.mark.django_db
@mock.patch("identify_file_format.executeOrRun")
def test_job_updates_file_format_version(
    execute_or_run: mock.Mock,
    job: mock.Mock,
    sip_file: models.File,
    format: fprmodels.Format,
    sip_file_format_version: models.FileFormatVersion,
) -> None:
    command_output = "fmt/111"
    execute_or_run.return_value = (0, command_output, "")

    fprmodels.FormatVersion.objects.filter(pronom_id=command_output).delete()
    format_version = fprmodels.FormatVersion.objects.create(
        format=format, pronom_id=command_output
    )

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.SUCCESS)
    assert (
        models.FileFormatVersion.objects.filter(
            file_uuid=sip_file, format_version=format_version
        ).count()
        == 1
    )


@pytest.mark.django_db
@mock.patch("identify_file_format.executeOrRun")
def test_job_adds_successful_format_identification_data(
    execute_or_run: mock.Mock,
    job: mock.Mock,
    sip_file: models.File,
    idcommand: fprmodels.IDCommand,
    format_version: fprmodels.Format,
) -> None:
    command_output = "fmt/111"
    execute_or_run.return_value = (0, command_output, "")

    fprmodels.FormatVersion.objects.filter(pronom_id=command_output).delete()
    format_version.pronom_id = command_output
    format_version.save()

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.SUCCESS)
    assert (
        models.Event.objects.filter(
            file_uuid=sip_file.uuid,
            event_type="format identification",
            event_detail=f'program="{idcommand.tool.description}"; version="{idcommand.tool.version}"',
            event_outcome="Positive",
            event_outcome_detail=command_output,
        ).count()
        == 1
    )
    assert (
        models.FileID.objects.filter(
            file=sip_file,
            format_name=format_version.format.description,
            format_version="",
            format_registry_name="PRONOM",
            format_registry_key=format_version.pronom_id,
        ).count()
        == 1
    )


@pytest.mark.django_db
@mock.patch("identify_file_format.executeOrRun")
def test_job_falls_back_to_identification_rule_if_format_version_does_not_exist(
    execute_or_run: mock.Mock,
    job: mock.Mock,
    sip_file: models.File,
    idcommand: fprmodels.IDCommand,
    idrule: fprmodels.IDRule,
) -> None:
    command_output = ".mp3"
    execute_or_run.return_value = (0, command_output, "")

    idcommand.config = ""
    idcommand.save()

    fprmodels.IDRule.objects.filter(command_output=command_output).delete()
    idrule.command_output = command_output
    idrule.save()

    identify_file_format.call([job])

    job.set_status.assert_called_once_with(identify_file_format.SUCCESS)
    assert (
        models.FileID.objects.filter(
            file=sip_file,
            format_name="",
            format_version="",
            format_registry_name="Archivematica Format Policy Registry",
            format_registry_key=command_output,
        ).count()
        == 1
    )
