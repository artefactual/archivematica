from unittest import mock

import characterize_file
import pytest
from client.job import Job
from fpr import models as fprmodels
from main import models


@pytest.fixture
def file(sip):
    location = b"%SIPDirectory%objects/file.mp3"
    return models.File.objects.create(
        sip=sip,
        filegrpuse="original",
        currentlocation=location,
        originallocation=location,
    )


@pytest.fixture
def format_version(db):
    return fprmodels.FormatVersion.objects.create(
        format=fprmodels.Format.objects.create()
    )


@pytest.fixture
def file_format_version(file, format_version):
    return models.FileFormatVersion.objects.create(
        file_uuid=file, format_version=format_version
    )


@pytest.fixture
def rule(format_version):
    return fprmodels.FPRule.objects.create(
        command=fprmodels.FPCommand.objects.create(),
        format=format_version,
        purpose="characterization",
    )


@pytest.fixture
def rule_with_xml_output_format(format_version):
    return fprmodels.FPRule.objects.create(
        command=fprmodels.FPCommand.objects.create(
            output_format=fprmodels.FormatVersion.objects.get(pronom_id="fmt/101")
        ),
        format=format_version,
        purpose="characterization",
    )


@pytest.fixture
def command_output(file, rule):
    return models.FPCommandOutput.objects.create(file=file, rule=rule)


@pytest.fixture
def delete_characterization_rules(db):
    fprmodels.FPRule.objects.filter(
        purpose__in=["characterization", "default_characterization"]
    ).delete()


@pytest.mark.django_db
def test_job_succeeds_if_file_is_already_characterized(file, sip, command_output):
    job = mock.Mock(
        args=["characterize_file", "file_path_not_used", str(file.uuid), str(sip.uuid)],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    characterize_file.call([job])

    job.set_status.assert_called_once_with(0)


@pytest.mark.django_db
def test_job_succeeds_if_no_characterization_rules_exist(
    file, sip, delete_characterization_rules
):
    job = mock.Mock(
        args=["characterize_file", "file_path_not_used", str(file.uuid), str(sip.uuid)],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    characterize_file.call([job])

    job.set_status.assert_called_once_with(0)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "script_type",
    ["bashScript", "pythonScript"],
    ids=["bashScript", "pythonScript"],
)
@mock.patch("characterize_file.executeOrRun")
def test_job_executes_command(
    execute_or_run, script_type, file, sip, rule, file_format_version
):
    rule.command.script_type = script_type
    rule.command.save()
    exit_code = 0
    stdout = "hello"
    stderr = ""
    execute_or_run.return_value = (exit_code, stdout, stderr)
    job = mock.Mock(
        args=["characterize_file", "file_path_not_used", str(file.uuid), str(sip.uuid)],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    characterize_file.call([job])

    job.set_status.assert_called_once_with(0)
    job.write_output.assert_called_once_with(stdout)
    assert job.write_error.mock_calls == [
        mock.call(stderr),
        mock.call(
            f'Tool output for command "{rule.command.description}" ({rule.command.uuid}) is not XML; not saving to database'
        ),
    ]


@pytest.mark.django_db
@mock.patch("characterize_file.executeOrRun")
def test_job_fails_if_command_fails(
    execute_or_run, file, sip, rule, file_format_version
):
    exit_code = 1
    stdout = ""
    stderr = "error!"
    execute_or_run.return_value = (exit_code, stdout, stderr)
    job = mock.Mock(
        args=["characterize_file", "file_path_not_used", str(file.uuid), str(sip.uuid)],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    characterize_file.call([job])

    job.set_status.assert_called_once_with(255)
    job.write_output.assert_called_once_with(stdout)
    assert job.write_error.mock_calls == [
        mock.call(stderr),
        mock.call(
            f"Command {rule.command.description} failed with exit status {exit_code}; stderr:"
        ),
    ]


@pytest.mark.django_db
@mock.patch("characterize_file.insertIntoFPCommandOutput")
@mock.patch("characterize_file.etree")
@mock.patch("characterize_file.executeOrRun")
def test_job_saves_valid_xml_command_output(
    execute_or_run,
    etree,
    insert_into_fp_command_output,
    file,
    sip,
    rule_with_xml_output_format,
    file_format_version,
):
    exit_code = 0
    stdout = "<mock>success</mock>"
    stderr = ""
    execute_or_run.return_value = (exit_code, stdout, stderr)
    job = mock.Mock(
        args=["characterize_file", "file_path_not_used", str(file.uuid), str(sip.uuid)],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    characterize_file.call([job])

    job.set_status.assert_called_once_with(0)
    assert job.write_output.mock_calls == [
        mock.call(stdout),
        mock.call(
            f'Saved XML output for command "{rule_with_xml_output_format.command.description}" ({rule_with_xml_output_format.command.uuid})'
        ),
    ]
    job.write_error.assert_called_once_with(stderr)
    etree.fromstring.assert_called_once_with(stdout.encode())
    insert_into_fp_command_output.assert_called_once_with(
        str(file.uuid), stdout, rule_with_xml_output_format.uuid
    )


@pytest.mark.django_db
@mock.patch("characterize_file.executeOrRun")
def test_job_fails_with_invalid_xml_command_output(
    execute_or_run,
    file,
    sip,
    rule_with_xml_output_format,
    file_format_version,
):
    exit_code = 0
    stdout = "invalid xml"
    stderr = ""
    execute_or_run.return_value = (exit_code, stdout, stderr)
    job = mock.Mock(
        args=["characterize_file", "file_path_not_used", str(file.uuid), str(sip.uuid)],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    characterize_file.call([job])

    job.set_status.assert_called_once_with(255)
    job.write_output.assert_called_once_with(stdout)
    assert job.write_error.mock_calls == [
        mock.call(stderr),
        mock.call(
            f'XML output for command "{rule_with_xml_output_format.command.description}" ({rule_with_xml_output_format.command.uuid}) was not valid XML; not saving to database'
        ),
    ]
