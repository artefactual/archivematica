import json
import pathlib
import uuid
from unittest import mock

import policy_check
import pytest
from client.job import Job
from fpr import models as fprmodels
from main import models


@pytest.fixture()
def sip(sip: models.SIP) -> models.SIP:
    # ReplacementDict expands SIP paths based on the shared directory.
    sip.currentpath = "%sharedPath%"
    sip.save()
    return sip


@pytest.fixture()
def preservation_file(preservation_file: models.File) -> models.File:
    preservation_file.filegrpuse = "preservation"
    preservation_file.save()
    return preservation_file


@pytest.fixture
def event(sip_file: models.SIP) -> models.Event:
    return models.Event.objects.create(file_uuid=sip_file, event_type="normalization")


@pytest.fixture
def derivation_for_preservation(
    sip_file: models.File, preservation_file: models.File, event: models.Event
) -> models.Derivation:
    return models.Derivation.objects.create(
        source_file=sip_file, derived_file=preservation_file, event=event
    )


@pytest.fixture
def preservation_file_format_version(
    preservation_file: models.File, format_version: fprmodels.FormatVersion
) -> models.FileFormatVersion:
    return models.FileFormatVersion.objects.create(
        file_uuid=preservation_file, format_version=format_version
    )


@pytest.fixture
def access_file(sip: models.SIP, transfer: models.Transfer) -> models.File:
    location = b"%SIPDirectory%objects/file.wav"
    return models.File.objects.create(
        transfer=transfer,
        sip=sip,
        filegrpuse="access",
        originallocation=location,
        currentlocation=location,
    )


@pytest.fixture
def derivation_for_access(
    sip_file: models.File, access_file: models.File
) -> models.Derivation:
    return models.Derivation.objects.create(
        source_file=sip_file, derived_file=access_file
    )


@pytest.fixture
def access_file_format_version(
    access_file: models.File, format_version: fprmodels.FormatVersion
) -> models.FileFormatVersion:
    return models.FileFormatVersion.objects.create(
        file_uuid=access_file, format_version=format_version
    )


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_succeeds_if_rules_exist(
    execute_or_run: mock.Mock,
    sip_file: models.File,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    job = mock.Mock(
        args=[
            "policy_check",
            sip_file.currentlocation.decode(),
            str(sip_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            sip_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )
    expected_stdout = json.dumps(
        {
            "eventOutcomeInformation": "pass",
            "eventOutcomeDetailNote": f'format="{format.description}"; version="{format_version.version}"; result="Well-Formed and valid"',
        }
    )
    execute_or_run.return_value = (0, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.SUCCESS_CODE)
    assert (
        models.Event.objects.filter(
            file_uuid_id=sip_file.uuid,
            event_type="validation",
            event_detail=(
                f'program="{fprule_policy_check.command.tool.description}";'
                f' version="{fprule_policy_check.command.tool.version}"'
            ),
            event_outcome="pass",
            event_outcome_detail=json.loads(expected_stdout)["eventOutcomeDetailNote"],
        ).count()
        == 1
    )
    assert job.pyprint.mock_calls == [
        mock.call("Running", fprule_policy_check.command.description),
        mock.call(
            f"Command {fprule_policy_check.command.description} completed with output {expected_stdout}"
        ),
        mock.call(
            f"Creating policy checking event for {sip_file.currentlocation.decode()} ({sip_file.uuid})"
        ),
    ]


@pytest.mark.django_db
@mock.patch(
    "policy_check.executeOrRun",
    return_value=(
        1,
        json.dumps(
            {"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}
        ),
        "",
    ),
)
def test_policy_checker_warns_if_rules_do_not_exist(
    execute_or_run: mock.Mock,
    sip_file: models.File,
    sip: models.SIP,
    sip_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    job = mock.Mock(
        args=[
            "policy_check",
            sip_file.currentlocation.decode(),
            str(sip_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            sip_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.NOT_APPLICABLE_CODE)

    job.pyprint.assert_called_once_with(
        "Not performing a policy check because there are no relevant FPR rules"
    )


@pytest.mark.django_db
@mock.patch(
    "policy_check.executeOrRun",
    return_value=(
        1,
        json.dumps(
            {"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}
        ),
        "",
    ),
)
def test_policy_checker_warns_if_file_does_not_exist(
    execute_or_run: mock.Mock,
    sip_file: models.File,
    sip: models.SIP,
    sip_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    file_uuid = str(uuid.uuid4())
    job = mock.Mock(
        args=[
            "policy_check",
            "",
            file_uuid,
            str(sip.uuid),
            str(shared_directory_path),
            sip_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.NOT_APPLICABLE_CODE)

    job.pyprint.assert_called_once_with(
        f"Not performing a policy check because there is no file with UUID {file_uuid}."
    )


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_fails_if_rule_command_fails(
    execute_or_run: mock.Mock,
    sip_file: models.File,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    job = mock.Mock(
        args=[
            "policy_check",
            sip_file.currentlocation.decode(),
            str(sip_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            sip_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )
    status = 1
    expected_stdout = json.dumps(
        {"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}
    )
    stderr = ""
    execute_or_run.return_value = (status, expected_stdout, stderr)

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.FAIL_CODE)
    assert job.pyprint.mock_calls == [
        mock.call("Running", fprule_policy_check.command.description)
    ]
    job.print_error.assert_called_once_with(
        f"Command {fprule_policy_check.command.description} failed with exit status {status}; stderr:",
        stderr,
    )


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_fails_if_event_outcome_information_in_output_is_not_pass(
    execute_or_run: mock.Mock,
    sip_file: models.File,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    event_outcome_information = "foobar"
    event_outcome_detail_note = "a note"
    expected_stdout = json.dumps(
        {
            "eventOutcomeInformation": event_outcome_information,
            "eventOutcomeDetailNote": event_outcome_detail_note,
        }
    )
    execute_or_run.return_value = (0, expected_stdout, "")
    job = mock.Mock(
        args=[
            "policy_check",
            sip_file.currentlocation.decode(),
            str(sip_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            sip_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.FAIL_CODE)

    assert job.print_error.mock_calls == [
        mock.call(
            f"Command {fprule_policy_check.command.description} returned a non-pass outcome for the policy check;\n\noutcome: {event_outcome_information}\n\ndetails: {event_outcome_detail_note}."
        )
    ]


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_verifies_file_type_is_preservation(
    execute_or_run: mock.Mock,
    derivation_for_preservation: models.Derivation,
    preservation_file: models.File,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    preservation_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    job = mock.Mock(
        args=[
            "policy_check",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )
    expected_stdout = json.dumps(
        {"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}
    )
    execute_or_run.return_value = (0, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.SUCCESS_CODE)
    assert job.pyprint.mock_calls == [
        mock.call("Running", ""),
        mock.call(
            f"Command {fprule_policy_check.command.description} completed with output {expected_stdout}"
        ),
        mock.call(
            f"Creating policy checking event for {preservation_file.currentlocation.decode()} ({preservation_file.uuid})"
        ),
    ]


@pytest.mark.django_db
@mock.patch(
    "policy_check.executeOrRun",
    return_value=(
        0,
        json.dumps(
            {"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}
        ),
        "",
    ),
)
def test_policy_checker_fails_if_file_is_not_preservation_derivative(
    execute_or_run: mock.Mock,
    preservation_file: models.File,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    preservation_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    job = mock.Mock(
        args=[
            "policy_check",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.NOT_APPLICABLE_CODE)
    assert job.pyprint.mock_calls == [
        mock.call(
            f"File {preservation_file.uuid} is not a preservation derivative; not performing a policy check."
        )
    ]


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_verifies_file_type_is_access(
    execute_or_run: mock.Mock,
    derivation_for_access: models.Derivation,
    access_file: models.File,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    access_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    job = mock.Mock(
        args=[
            "policy_check",
            access_file.currentlocation.decode(),
            str(access_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            access_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )
    expected_stdout = json.dumps(
        {"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}
    )
    execute_or_run.return_value = (0, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.SUCCESS_CODE)
    assert job.pyprint.mock_calls == [
        mock.call("Running", ""),
        mock.call(
            f"Command {fprule_policy_check.command.description} completed with output {expected_stdout}"
        ),
        mock.call(
            f"Creating policy checking event for {access_file.currentlocation.decode()} ({access_file.uuid})"
        ),
    ]


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_fails_if_file_is_not_access_derivative(
    execute_or_run: mock.Mock,
    access_file: models.File,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    access_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    job = mock.Mock(
        args=[
            "policy_check",
            access_file.currentlocation.decode(),
            str(access_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            access_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )
    expected_stdout = json.dumps(
        {
            "eventOutcomeInformation": "pass",
            "eventOutcomeDetailNote": f'format="{format.description}"; version="{format_version.version}"; result="Well-Formed and valid"',
        }
    )
    execute_or_run.return_value = (0, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.NOT_APPLICABLE_CODE)

    assert job.pyprint.mock_calls == [
        mock.call(
            f"File {access_file.uuid} is not an access derivative; not performing a policy check."
        ),
        mock.call(f"File {access_file.uuid} is not a derivative."),
    ]


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_saves_policy_check_result_into_logs_directory(
    execute_or_run: mock.Mock,
    preservation_file: models.File,
    derivation_for_preservation: models.Derivation,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    preservation_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    log_directory = shared_directory_path / "logs"
    log_directory.mkdir()
    policy_file_name = "MP3 has duration"
    stdout = "<mock>success</mock>"
    execute_or_run.return_value = (
        0,
        json.dumps(
            {
                "eventOutcomeInformation": "pass",
                "eventOutcomeDetailNote": "a note",
                "policy": "test",
                "policyFileName": policy_file_name,
                "stdout": stdout,
            }
        ),
        "",
    )
    job = mock.Mock(
        args=[
            "policy_check",
            preservation_file.currentlocation.decode(),
            str(preservation_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            preservation_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.SUCCESS_CODE)

    log_file = (
        log_directory
        / "policyChecks"
        / policy_file_name
        / f"{pathlib.Path(preservation_file.currentlocation.decode()).name}.xml"
    )
    assert log_file.exists()
    assert log_file.read_text() == stdout


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_saves_policy_check_result_into_submission_documentation_directory(
    execute_or_run: mock.Mock,
    sip_file: models.File,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    sip_file_format_version: models.FileFormatVersion,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    submission_documentation_directory = (
        shared_directory_path / "metadata" / "submissionDocumentation"
    )
    submission_documentation_directory.mkdir(parents=True)
    policy = "test"
    policy_file_name = "MP3 has duration"
    stdout = "<mock>success</mock>"
    execute_or_run.return_value = (
        0,
        json.dumps(
            {
                "eventOutcomeInformation": "pass",
                "eventOutcomeDetailNote": "a note",
                "policy": policy,
                "policyFileName": policy_file_name,
                "stdout": stdout,
            }
        ),
        "",
    )
    job = mock.Mock(
        args=[
            "policy_check",
            sip_file.currentlocation.decode(),
            str(sip_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            sip_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.SUCCESS_CODE)

    log_file = submission_documentation_directory / "policies" / policy_file_name
    assert log_file.exists()
    assert log_file.read_text() == policy


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_checks_manually_normalized_access_derivative_file(
    execute_or_run: mock.Mock,
    transfer: models.Transfer,
    sip_file: models.File,
    sip: models.SIP,
    fprule_policy_check: fprmodels.FPRule,
    format: fprmodels.Format,
    format_version: fprmodels.FormatVersion,
    shared_directory_path: pathlib.Path,
) -> None:
    expected_stdout = json.dumps(
        {"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}
    )

    execute_or_run.return_value = (0, expected_stdout, "")
    sip_file_name = pathlib.Path(sip_file.currentlocation.decode()).name
    manually_access_derivative_file = models.File.objects.create(
        transfer=transfer,
        sip=sip,
        filegrpuse="original",
        originallocation=f"%transferDirectory%objects/manualNormalization/access/{sip_file_name}".encode(),
    )
    models.FileFormatVersion.objects.create(
        file_uuid=manually_access_derivative_file, format_version=format_version
    )
    file_path = f"{shared_directory_path}/DIP/objects/{uuid.uuid4()}-{sip_file_name}"
    file_uuid = "None"
    job = mock.Mock(
        args=[
            "policy_check",
            file_path,
            file_uuid,
            str(sip.uuid),
            str(shared_directory_path),
            sip_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    policy_check.call([job])

    job.set_status.assert_called_once_with(policy_check.SUCCESS_CODE)
    assert job.pyprint.mock_calls == [
        mock.call("Running", fprule_policy_check.command.description),
        mock.call(
            f"Command {fprule_policy_check.command.description} completed with output {expected_stdout}"
        ),
        mock.call(f"Creating policy checking event for {file_path} ({file_uuid})"),
    ]
