import pytest
from client.job import Job
from fpr.models import Format
from fpr.models import FormatGroup
from fpr.models import FormatVersion
from fpr.models import FPCommand
from fpr.models import FPRule
from fpr.models import FPTool
from main.models import Event
from main.models import File
from main.models import FileFormatVersion
from main.models import SIP
from validate_file import main


@pytest.fixture
def sip(tmp_path):
    sip_dir = tmp_path / "sip"
    sip_dir.mkdir()
    # Create logs directory in the SIP.
    (sip_dir / "logs").mkdir()

    return SIP.objects.create(currentpath=str(sip_dir))


@pytest.fixture
def file_obj(tmp_path, sip):
    d = tmp_path / "dir"
    d.mkdir()
    txt_file = d / "file.txt"
    txt_file.write_text("hello world")

    return File.objects.create(
        sip=sip, originallocation=txt_file, currentlocation=txt_file
    )


@pytest.fixture
def format_version():
    format_group = FormatGroup.objects.create(description="a format group")
    format = Format.objects.create(description="a format", group=format_group)

    return FormatVersion.objects.create(description="a format 1.0", format=format)


@pytest.fixture
def command():
    tool = FPTool.objects.create(description="a tool")

    return FPCommand.objects.create(
        description="a command",
        script_type="pythonScript",
        command="script.py",
        tool=tool,
    )


@pytest.fixture
def fprule(format_version, command):
    return FPRule.objects.create(
        purpose=FPRule.VALIDATION, format=format_version, command=command
    )


@pytest.fixture
def file_format_version(file_obj, format_version):
    FileFormatVersion.objects.create(file_uuid=file_obj, format_version=format_version)


@pytest.mark.django_db
def test_main(
    mocker, sip, file_obj, format_version, fprule, command, file_format_version
):
    exit_status = 0
    stdout = '{"eventOutcomeInformation": "pass", "eventOutcomeDetailNote": "a note"}'
    stderr = ""
    execute_or_run = mocker.patch(
        "validate_file.executeOrRun", return_value=(exit_status, stdout, stderr)
    )
    job = mocker.Mock(spec=Job)
    file_type = "original"

    main(
        job=job,
        file_path=file_obj.currentlocation,
        file_uuid=file_obj.uuid,
        sip_uuid=sip.uuid,
        shared_path=sip.currentpath,
        file_type=file_type,
    )

    # Check the executed script.
    execute_or_run.assert_called_once_with(
        type=command.script_type,
        text=command.command,
        printing=False,
        arguments=[file_obj.currentlocation],
    )

    # Verify a PREMIS validation event was created with the output of the
    # validation command.
    assert (
        Event.objects.filter(
            file_uuid=file_obj.uuid,
            event_type="validation",
            event_outcome="pass",
            event_outcome_detail="a note",
        ).count()
        == 1
    )
