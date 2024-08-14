import json
import pathlib
import uuid
from pprint import pformat
from unittest import mock

import pytest
import pytest_django
import validate_file
from client.job import Job
from fpr import models as fprmodels
from main import models


@pytest.fixture
def sip(sip: models.SIP) -> models.SIP:
    sip.currentpath = r"%sharedPath%"
    sip.save()

    return sip


@pytest.fixture
def sip_logs_directory(
    sip: models.SIP, shared_directory_path: pathlib.Path
) -> pathlib.Path:
    result = (
        pathlib.Path(
            sip.currentpath.replace(r"%sharedPath%", str(shared_directory_path))
        )
        / "logs"
    )
    result.mkdir(parents=True)

    return result


@pytest.fixture
def preservation_file_format_version(
    preservation_file: models.File, format_version: fprmodels.FormatVersion
) -> models.FileFormatVersion:
    return models.FileFormatVersion.objects.create(
        file_uuid=preservation_file, format_version=format_version
    )


@pytest.fixture
def preservation_derivation(
    sip_file: models.File, preservation_file: models.File
) -> models.Derivation:
    return models.Derivation.objects.create(
        source_file=sip_file,
        derived_file=preservation_file,
        event=models.Event.objects.create(
            file_uuid=preservation_file, event_type="normalization"
        ),
    )


@pytest.mark.django_db
@mock.patch(
    "validate_file.executeOrRun",
    return_value=(
        0,
        json.dumps(
            {
                "eventOutcomeInformation": "pass",
                "eventOutcomeDetailNote": "a note",
                "stdout": "<root>output</root>",
            }
        ),
        "",
    ),
)
def test_job_warns_if_preservation_derivative_sip_does_not_exist(
    execute_or_run: mock.Mock,
    preservation_file: models.File,
    preservation_file_format_version: models.FileFormatVersion,
    preservation_derivation: models.Derivation,
    fprule_validation: fprmodels.FPRule,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    sip_uuid = uuid.uuid4()
    job = mock.Mock(
        args=[
            "validate_file.py",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip_uuid),
            str(settings.SHARED_DIRECTORY),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    validate_file.call([job])

    job.set_status.assert_called_once_with(validate_file.SUCCESS_CODE)

    job.print_error.assert_called_once_with(
        f"Warning: unable to retrieve SIP model corresponding to SIP UUID {sip_uuid}"
    )


@pytest.mark.django_db
@mock.patch(
    "validate_file.executeOrRun",
    return_value=(
        0,
        json.dumps(
            {
                "eventOutcomeInformation": "pass",
                "eventOutcomeDetailNote": "a note",
                "stdout": "<root>output</root>",
            }
        ),
        "",
    ),
)
def test_job_warns_if_preservation_derivative_sip_logs_directory_does_not_exist(
    execute_or_run: mock.Mock,
    sip: models.SIP,
    preservation_file: models.File,
    preservation_file_format_version: models.FileFormatVersion,
    preservation_derivation: models.Derivation,
    fprule_validation: fprmodels.FPRule,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    job = mock.Mock(
        args=[
            "validate_file.py",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(settings.SHARED_DIRECTORY),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    validate_file.call([job])

    job.set_status.assert_called_once_with(validate_file.SUCCESS_CODE)

    job.print_error.assert_called_once_with(
        f"Warning: unable to find a logs/ directory in the SIP with UUID {sip.uuid}"
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "outcome_information,validation_result",
    [("pass", "successful"), ("partial pass", "partially successful")],
    ids=["pass", "partial-pass"],
)
@mock.patch("validate_file.executeOrRun")
def test_job_succeeds_with_passing_validation_outcome(
    execute_or_run: mock.Mock,
    outcome_information: str,
    validation_result: str,
    sip: models.SIP,
    preservation_file: models.File,
    preservation_file_format_version: models.FileFormatVersion,
    preservation_derivation: models.Derivation,
    fprule_validation: fprmodels.FPRule,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    execute_or_run.return_value = (
        0,
        json.dumps(
            {
                "eventOutcomeInformation": outcome_information,
                "eventOutcomeDetailNote": "a note",
            }
        ),
        "",
    )
    job = mock.Mock(
        args=[
            "validate_file.py",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(settings.SHARED_DIRECTORY),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    validate_file.call([job])

    job.set_status.assert_called_once_with(validate_file.SUCCESS_CODE)

    assert job.print_output.mock_calls == [
        mock.call("Running", fprule_validation.command.description),
        mock.call(
            f'Command "{fprule_validation.command.description}" was {validation_result}'
        ),
        mock.call(
            f"Creating {fprule_validation.purpose} event for {preservation_file.currentlocation.decode()} ({preservation_file.uuid})"
        ),
    ]

    execute_or_run.assert_called_once_with(
        type=fprule_validation.command.script_type,
        text=fprule_validation.command.command,
        printing=False,
        arguments=[preservation_file.currentlocation.decode()],
    )

    assert (
        models.Event.objects.filter(
            file_uuid=preservation_file.uuid,
            event_type=fprule_validation.purpose,
            event_outcome=outcome_information,
            event_outcome_detail="a note",
        ).count()
        == 1
    )


@pytest.mark.django_db
@mock.patch("validate_file.executeOrRun")
def test_job_saves_command_output_as_preservation_logs(
    execute_or_run: mock.Mock,
    sip: models.SIP,
    preservation_file: models.File,
    preservation_file_format_version: models.FileFormatVersion,
    preservation_derivation: models.Derivation,
    fprule_validation: fprmodels.FPRule,
    settings: pytest_django.fixtures.SettingsWrapper,
    sip_logs_directory: pathlib.Path,
) -> None:
    stdout = "<root>output</root>"
    execute_or_run.return_value = (
        0,
        json.dumps(
            {
                "eventOutcomeInformation": "pass",
                "eventOutcomeDetailNote": "a note",
                "stdout": stdout,
            }
        ),
        "",
    )
    job = mock.Mock(
        args=[
            "validate_file.py",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(settings.SHARED_DIRECTORY),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    validate_file.call([job])

    job.set_status.assert_called_once_with(validate_file.SUCCESS_CODE)
    log_file = (
        sip_logs_directory
        / "implementationChecks"
        / f"{pathlib.Path(preservation_file.currentlocation.decode()).name}.xml"
    )
    assert log_file.exists()
    assert log_file.read_text() == stdout


@pytest.mark.django_db
@mock.patch(
    "validate_file.executeOrRun",
    return_value=(
        0,
        json.dumps(
            {
                "eventOutcomeInformation": "pass",
                "eventOutcomeDetailNote": "a note",
            }
        ),
        "",
    ),
)
def test_job_falls_back_to_default_validation_rule(
    execute_or_run: mock.Mock,
    sip: models.SIP,
    preservation_file: models.File,
    preservation_file_format_version: models.FileFormatVersion,
    preservation_derivation: models.Derivation,
    settings: pytest_django.fixtures.SettingsWrapper,
    fpcommand: fprmodels.FPCommand,
    format_version: fprmodels.FormatVersion,
) -> None:
    fpcommand.script_type = "bashScript"
    fpcommand.save()

    fprmodels.FPRule.objects.filter(purpose=fprmodels.FPRule.VALIDATION).delete()
    fprmodels.FPRule.objects.create(
        command=fpcommand,
        format=format_version,
        purpose=f"default_{fprmodels.FPRule.VALIDATION}",
    )
    job = mock.Mock(
        args=[
            "validate_file.py",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(settings.SHARED_DIRECTORY),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    validate_file.call([job])

    job.set_status.assert_called_once_with(validate_file.SUCCESS_CODE)

    execute_or_run.assert_called_once_with(
        type=fpcommand.script_type,
        text=fpcommand.command,
        printing=False,
        arguments=[],
    )

    assert job.print_output.mock_calls == [
        mock.call("Running", fpcommand.description),
        mock.call(f'Command "{fpcommand.description}" was successful'),
        mock.call(
            f"Creating {fprmodels.FPRule.VALIDATION} event for {preservation_file.currentlocation.decode()} ({preservation_file.uuid})"
        ),
    ]


@pytest.mark.django_db
def test_job_skips_validation_if_rules_do_not_exist(
    sip: models.SIP,
    sip_file: models.File,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    fprmodels.FPRule.objects.filter(purpose=fprmodels.FPRule.VALIDATION)

    job = mock.Mock(
        args=[
            "validate_file.py",
            sip_file.currentlocation.decode(),
            str(sip_file.uuid),
            str(sip.uuid),
            str(settings.SHARED_DIRECTORY),
            sip_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    validate_file.call([job])

    job.set_status.assert_called_once_with(validate_file.NO_RULES_CODE)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "file_type,error",
    [
        ("preservation", "is not a preservation derivative"),
        ("access", "is not an access derivative"),
    ],
    ids=["preservation", "access"],
)
def test_job_skips_validation_if_file_is_not_a_derivative(
    file_type: str,
    error: str,
    sip: models.SIP,
    preservation_file: models.File,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    preservation_file.filegrpuse = file_type
    preservation_file.save()

    job = mock.Mock(
        args=[
            "validate_file.py",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(settings.SHARED_DIRECTORY),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    validate_file.call([job])

    job.set_status.assert_called_once_with(validate_file.NOT_DERIVATIVE_CODE)

    job.print_output.assert_called_once_with(
        f"File {preservation_file.uuid} {error}; not validating."
    )


@pytest.mark.django_db
@mock.patch("validate_file.executeOrRun")
def test_job_fails_if_rule_command_fails(
    execute_or_run: mock.Mock,
    sip: models.SIP,
    preservation_file: models.File,
    preservation_file_format_version: models.FileFormatVersion,
    preservation_derivation: models.Derivation,
    fprule_validation: fprmodels.FPRule,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    exit_status = -1
    stderr = "error!"
    execute_or_run.return_value = (exit_status, "", stderr)
    job = mock.Mock(
        args=[
            "validate_file.py",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(settings.SHARED_DIRECTORY),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    validate_file.call([job])

    job.set_status.assert_called_once_with(validate_file.FAIL_CODE)

    job.print_error.assert_called_once_with(
        f"Command {fprule_validation.command.description} failed with exit status {exit_status};"
        f" stderr: {stderr}"
    )


@pytest.mark.django_db
@mock.patch("validate_file.executeOrRun")
def test_job_fails_with_non_passing_validation_outcome(
    execute_or_run: mock.Mock,
    sip: models.SIP,
    preservation_file: models.File,
    preservation_file_format_version: models.FileFormatVersion,
    preservation_derivation: models.Derivation,
    fprule_validation: fprmodels.FPRule,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    stdout = json.dumps(
        {
            "eventOutcomeInformation": "fail",
            "eventOutcomeDetailNote": "a note",
        }
    )
    execute_or_run.return_value = (0, stdout, "")
    job = mock.Mock(
        args=[
            "validate_file.py",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(settings.SHARED_DIRECTORY),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    validate_file.call([job])

    job.set_status.assert_called_once_with(validate_file.FAIL_CODE)

    assert job.print_output.mock_calls == [
        mock.call("Running", fprule_validation.command.description),
        mock.call(
            f"Creating {fprule_validation.purpose} event for {preservation_file.currentlocation.decode()} ({preservation_file.uuid})"
        ),
    ]

    job.pyprint.assert_called_once_with(
        f"Command {fprule_validation.command.description} indicated failure with this output:\n\n{pformat(stdout)}",
        file=mock.ANY,
    )
