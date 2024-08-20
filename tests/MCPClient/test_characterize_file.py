from unittest import mock

import characterize_file
import pytest
from client.job import Job
from fpr import models as fprmodels
from main import models


@pytest.fixture
def rule_with_xml_output_format(
    format_version: fprmodels.FormatVersion,
) -> fprmodels.FPRule:
    return fprmodels.FPRule.objects.create(
        command=fprmodels.FPCommand.objects.create(
            output_format=fprmodels.FormatVersion.objects.get(pronom_id="fmt/101")
        ),
        format=format_version,
        purpose="characterization",
    )


@pytest.fixture
def fpcommand_output(
    sip_file: models.File, fprule_characterization: fprmodels.FPRule
) -> models.FPCommandOutput:
    return models.FPCommandOutput.objects.create(
        file=sip_file, rule=fprule_characterization
    )


@pytest.fixture
def delete_characterization_rules() -> None:
    fprmodels.FPRule.objects.filter(
        purpose__in=["characterization", "default_characterization"]
    ).delete()


@pytest.mark.django_db
def test_job_succeeds_if_file_is_already_characterized(
    sip_file: models.File, sip: models.SIP, fpcommand_output: models.FPCommandOutput
) -> None:
    job = mock.Mock(
        args=[
            "characterize_file",
            str(sip_file.uuid),
            str(sip.uuid),
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    characterize_file.call([job])

    job.set_status.assert_called_once_with(0)


@pytest.mark.django_db
def test_job_succeeds_if_no_characterization_rules_exist(
    sip_file: models.File, sip: models.SIP, delete_characterization_rules: None
) -> None:
    job = mock.Mock(
        args=[
            "characterize_file",
            str(sip_file.uuid),
            str(sip.uuid),
        ],
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
    execute_or_run: mock.Mock,
    script_type: str,
    sip_file: models.File,
    sip: models.SIP,
    fprule_characterization: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
) -> None:
    fprule_characterization.command.script_type = script_type
    fprule_characterization.command.save()
    exit_code = 0
    stdout = "hello"
    stderr = ""
    execute_or_run.return_value = (exit_code, stdout, stderr)
    job = mock.Mock(
        args=[
            "characterize_file",
            str(sip_file.uuid),
            str(sip.uuid),
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    characterize_file.call([job])

    job.set_status.assert_called_once_with(0)
    job.write_output.assert_called_once_with(stdout)
    assert job.write_error.mock_calls == [
        mock.call(stderr),
        mock.call(
            f'Tool output for command "{fprule_characterization.command.description}" ({fprule_characterization.command.uuid}) is not XML; not saving to database'
        ),
    ]


@pytest.mark.django_db
@mock.patch("characterize_file.executeOrRun")
def test_job_fails_if_command_fails(
    execute_or_run: mock.Mock,
    sip_file: models.File,
    sip: models.SIP,
    fprule_characterization: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
) -> None:
    exit_code = 1
    stdout = ""
    stderr = "error!"
    execute_or_run.return_value = (exit_code, stdout, stderr)
    job = mock.Mock(
        args=[
            "characterize_file",
            str(sip_file.uuid),
            str(sip.uuid),
        ],
        spec=Job,
    )
    job.JobContext = mock.MagicMock()

    characterize_file.call([job])

    job.set_status.assert_called_once_with(255)
    job.write_output.assert_called_once_with(stdout)
    assert job.write_error.mock_calls == [
        mock.call(stderr),
        mock.call(
            f"Command {fprule_characterization.command.description} failed with exit status {exit_code}; stderr:"
        ),
    ]


@pytest.mark.django_db
@mock.patch("characterize_file.insertIntoFPCommandOutput")
@mock.patch("characterize_file.etree")
@mock.patch("characterize_file.executeOrRun")
def test_job_saves_valid_xml_command_output(
    execute_or_run: mock.Mock,
    etree: mock.Mock,
    insert_into_fp_command_output: mock.Mock,
    sip_file: models.File,
    sip: models.SIP,
    rule_with_xml_output_format: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
) -> None:
    exit_code = 0
    stdout = "<mock>success</mock>"
    stderr = ""
    execute_or_run.return_value = (exit_code, stdout, stderr)
    job = mock.Mock(
        args=[
            "characterize_file",
            str(sip_file.uuid),
            str(sip.uuid),
        ],
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
        sip_file.uuid, stdout, rule_with_xml_output_format.uuid
    )


@pytest.mark.django_db
@mock.patch("characterize_file.executeOrRun")
def test_job_fails_with_invalid_xml_command_output(
    execute_or_run: mock.Mock,
    sip_file: models.File,
    sip: models.SIP,
    rule_with_xml_output_format: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
) -> None:
    exit_code = 0
    stdout = "invalid xml"
    stderr = ""
    execute_or_run.return_value = (exit_code, stdout, stderr)
    job = mock.Mock(
        args=[
            "characterize_file",
            str(sip_file.uuid),
            str(sip.uuid),
        ],
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
