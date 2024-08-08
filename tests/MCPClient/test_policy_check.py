import json
import pathlib
import uuid
from unittest import mock

import policy_check
import pytest
from client.job import Job
from main import models


@pytest.fixture()
def sip(sip):
    # ReplacementDict expands SIP paths based on the shared directory.
    sip.currentpath = "%sharedPath%"
    sip.save()
    return sip


@pytest.fixture()
def preservation_file(preservation_file):
    preservation_file.filegrpuse = "preservation"
    preservation_file.save()
    return preservation_file


@pytest.fixture
def event(sip_file):
    return models.Event.objects.create(file_uuid=sip_file, event_type="normalization")


@pytest.fixture
def derivation_for_preservation(sip_file, preservation_file, event):
    return models.Derivation.objects.create(
        source_file=sip_file, derived_file=preservation_file, event=event
    )


@pytest.fixture
def preservation_file_format_version(preservation_file, format_version):
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
def derivation_for_access(sip_file, access_file):
    return models.Derivation.objects.create(
        source_file=sip_file, derived_file=access_file
    )


@pytest.fixture
def access_file_format_version(access_file, format_version):
    return models.FileFormatVersion.objects.create(
        file_uuid=access_file, format_version=format_version
    )


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_check_if_rules_exist(
    execute_or_run,
    sip_file,
    sip,
    fprule_policy_check,
    sip_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
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

    job.set_status.assert_called_once_with(0)
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
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_check_if_no_rules_exist(
    execute_or_run,
    sip_file,
    sip,
    sip_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
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

    job.set_status.assert_called_once_with(0)

    job.pyprint.assert_called_once_with(
        "Not performing a policy check because there are no relevant FPR rules"
    )


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_check_if_file_does_not_exist(
    execute_or_run,
    sip_file,
    sip,
    sip_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
    job = mock.Mock(
        args=[
            "policy_check",
            "",
            "",
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

    job.set_status.assert_called_once_with(0)

    job.pyprint.assert_called_once_with(
        "Not performing a policy check because there is no file with UUID ."
    )


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_execute_rule_command_returns_failed(
    execute_or_run,
    sip_file,
    sip,
    fprule_policy_check,
    sip_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
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
    execute_or_run.return_value = (1, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(1)
    assert job.pyprint.mock_calls == [
        mock.call("Running", fprule_policy_check.command.description)
    ]
    job.print_error.assert_called_once_with(
        f"Command {fprule_policy_check.command.description} failed with exit status 1; stderr:",
        "",
    )


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_execute_rule_command_returns_failed_if_event_outcome_information_other_than_pass(
    execute_or_run,
    sip_file,
    sip,
    fprule_policy_check,
    sip_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
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
            "eventOutcomeInformation": "",
            "eventOutcomeDetailNote": "",
        }
    )
    execute_or_run.return_value = (0, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(1)


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_check_verifies_file_type_is_preservation(
    execute_or_run,
    derivation_for_preservation,
    preservation_file,
    sip,
    fprule_policy_check,
    preservation_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
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
        {
            "eventOutcomeInformation": "pass",
            "eventOutcomeDetailNote": f'format="{format.description}"; version="{format_version.version}"; result="Well-Formed and valid"',
        }
    )
    execute_or_run.return_value = (0, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(0)
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
@mock.patch("policy_check.executeOrRun")
def test_policy_check_fails_if_file_is_not_preservation_derivative(
    execute_or_run,
    preservation_file,
    sip,
    fprule_policy_check,
    preservation_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
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
        {
            "eventOutcomeInformation": "pass",
            "eventOutcomeDetailNote": f'format="{format.description}"; version="{format_version.version}"; result="Well-Formed and valid"',
        }
    )
    execute_or_run.return_value = (0, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(0)
    assert job.pyprint.mock_calls == [
        mock.call(
            f"File {preservation_file.uuid} is not a preservation derivative; not performing a policy check."
        )
    ]


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_check_verifies_file_type_is_access(
    execute_or_run,
    derivation_for_access,
    access_file,
    sip,
    fprule_policy_check,
    access_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
    job = mock.Mock(
        args=[
            "policy_check",
            access_file.currentlocation.decode(),
            str(access_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            "access",
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

    job.set_status.assert_called_once_with(0)
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
def test_policy_check_fails_if_file_is_not_access_derivative(
    execute_or_run,
    access_file,
    sip,
    fprule_policy_check,
    access_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
    job = mock.Mock(
        args=[
            "policy_check",
            access_file.currentlocation.decode(),
            str(access_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            "access",
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

    job.set_status.assert_called_once_with(0)

    assert job.pyprint.mock_calls == [
        mock.call(
            f"File {access_file.uuid} is not an access derivative; not performing a policy check."
        ),
        mock.call(f"File {access_file.uuid} is not a derivative."),
    ]


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_saves_policy_check_result_into_logs_directory(
    execute_or_run,
    sip_file,
    sip,
    fprule_policy_check,
    sip_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
    log_directory = shared_directory_path / "logs"
    log_directory.mkdir()
    job = mock.Mock(
        args=[
            "policy_check",
            sip_file.currentlocation.decode(),
            str(sip_file.uuid),
            str(sip.uuid),
            str(shared_directory_path),
            "preservation",
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )
    expected_stdout = json.dumps(
        {
            "eventOutcomeInformation": "pass",
            "eventOutcomeDetailNote": "MediaConch policy check result against policy file MP3 has duration: All policy checks passed: Does the audio duration exist?; MP3 has duration",
            "policy": '<?xml version="1.0"?>\n<policy type="and" name="MP3 has duration" license="CC-BY-SA-4.0+">\n  <description>Rudimentary test to check for an MP3 having a duration value.</description>\n  <rule name="Does the audio duration exist?" value="Duration" tracktype="General" occurrence="*" operator="exists">mp3</rule>\n</policy>',
            "policyFileName": "MP3 has duration",
            "stdout": "<root>foobar</root>",
        }
    )
    execute_or_run.return_value = (0, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(0)


@pytest.mark.django_db
@mock.patch("policy_check.executeOrRun")
def test_policy_checker_saves_policy_check_result_into_submission_documentation_directory(
    execute_or_run,
    sip_file,
    sip,
    fprule_policy_check,
    sip_file_format_version,
    format,
    format_version,
    shared_directory_path,
):
    submission_documentation_directory = (
        shared_directory_path / "metadata" / "submissionDocumentation"
    )
    submission_documentation_directory.mkdir(parents=True)
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
            "eventOutcomeDetailNote": "MediaConch policy check result against policy file MP3 has duration: All policy checks passed: Does the audio duration exist?; MP3 has duration",
            "policy": '<?xml version="1.0"?>\n<policy type="and" name="MP3 has duration" license="CC-BY-SA-4.0+">\n  <description>Rudimentary test to check for an MP3 having a duration value.</description>\n  <rule name="Does the audio duration exist?" value="Duration" tracktype="General" occurrence="*" operator="exists">mp3</rule>\n</policy>',
            "policyFileName": "MP3 has duration",
            "stdout": "<root>foobar</root>",
        }
    )
    execute_or_run.return_value = (0, expected_stdout, "")

    policy_check.call([job])

    job.set_status.assert_called_once_with(0)


@pytest.mark.django_db
@mock.patch(
    "policy_check.executeOrRun",
    return_value=(
        0,
        json.dumps({"eventOutcomeInformation": "pass"}),
        "",
    ),
)
def test_policy_checker_checks_manually_normalized_access_derivative_file(
    execute_or_run,
    transfer,
    sip_file,
    sip,
    fprule_policy_check,
    format,
    format_version,
    shared_directory_path,
):
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
    job = mock.Mock(
        args=[
            "policy_check",
            f"{shared_directory_path}/DIP/objects/{uuid.uuid4()}-{sip_file_name}",
            "None",
            str(sip.uuid),
            str(shared_directory_path),
            sip_file.filegrpuse,
        ],
        JobContext=mock.MagicMock(),
        spec=Job,
    )

    policy_check.call([job])

    job.set_status.assert_called_once_with(0)
