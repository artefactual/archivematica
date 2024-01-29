from pathlib import Path

import has_packages
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
from main.models import Transfer


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
def extract_fprule(format_version, command):
    return FPRule.objects.create(
        purpose=FPRule.EXTRACTION, format=format_version, command=command
    )


@pytest.fixture
def transfer(tmp_path):
    transfer_dir = tmp_path / "transfer"
    transfer_dir.mkdir()

    return Transfer.objects.create(currentlocation=str(transfer_dir))


@pytest.fixture
def compressed_file(transfer, format_version):
    # Simulate a compressed file being extracted to a directory with the same name.
    d = Path(transfer.currentlocation) / "compressed.zip"
    d.mkdir()

    # Place an extracted file in it.
    f = d / "file.txt"
    f.touch()

    # Create File models for the compressed and extracted files.
    result = File.objects.create(
        transfer=transfer, originallocation=bytes(d), currentlocation=bytes(d)
    )
    File.objects.create(
        transfer=transfer, originallocation=bytes(f), currentlocation=bytes(f)
    )

    # Create a file format version for the compressed file.
    FileFormatVersion.objects.create(file_uuid=result, format_version=format_version)

    return result


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rule_purpose,expected_exit_code",
    [(FPRule.EXTRACTION, 0), (FPRule.CHARACTERIZATION, 1)],
    ids=["extract_rule", "not_extract_rule"],
)
def test_main_detects_file_is_extractable_based_on_extract_fpr_rule(
    mocker,
    transfer,
    compressed_file,
    format_version,
    command,
    rule_purpose,
    expected_exit_code,
):
    job = mocker.Mock(spec=Job)
    FPRule.objects.create(purpose=rule_purpose, format=format_version, command=command)

    result = has_packages.main(job, str(transfer.uuid))

    assert result == expected_exit_code


@pytest.mark.django_db
@pytest.mark.parametrize(
    "event_type,expected_exit_code",
    [("unpacking", 1), ("charaterization", 0)],
    ids=["unpacking_event", "not_unpacking_event"],
)
def test_main_detects_file_was_already_extracted_from_unpacking_event(
    mocker,
    transfer,
    compressed_file,
    format_version,
    command,
    extract_fprule,
    event_type,
    expected_exit_code,
):
    job = mocker.Mock(spec=Job)
    extracted_file = File.objects.get(
        currentlocation__startswith=compressed_file.currentlocation.decode(),
        currentlocation__endswith="file.txt",
    )
    Event.objects.create(
        file_uuid=extracted_file,
        event_type=event_type,
        event_detail=f"Unpacked from: {extracted_file.currentlocation} ({compressed_file.uuid})",
    )

    result = has_packages.main(job, str(transfer.uuid))

    assert result == expected_exit_code
