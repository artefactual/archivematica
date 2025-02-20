import re

import pytest
from executeOrRunSubProcess import executeOrRun
from fpr.models import FPCommand


@pytest.mark.django_db
def test_7z_extraction_event_detail_command_returns_7z_version() -> None:
    expected_program = "7z"
    # The event detail command extracts different lines depending on the 7z version.
    # Older versions report the version on a line starting with "p7zip Version"
    # while more recent versions use a line starting with "7-Zip".
    expected_version_pattern = r"(^p7zip Version|^7-Zip)"
    filters = {
        "command_usage": "event_detail",
        "description": "Get event detail text for 7z extraction",
    }
    command = FPCommand.active.get(**filters)

    _, output, _ = executeOrRun(command.script_type, command.command)

    match = re.search(r'program="(?P<program>.*?)"; version="(?P<version>.*?)"', output)
    assert match is not None
    result = match.groupdict()
    assert result["program"] == expected_program
    assert re.search(expected_version_pattern, result["version"]) is not None


@pytest.mark.django_db
def test_convert_event_detail_command_returns_convert_version() -> None:
    expected_program = "convert"
    expected_version_pattern = r"^Version: ImageMagick"
    filters = {
        "command_usage": "event_detail",
        "description": "convert event detail",
    }
    command = FPCommand.active.get(**filters)

    _, output, _ = executeOrRun(command.script_type, command.command)

    match = re.search(r'program="(?P<program>.*?)"; version="(?P<version>.*?)"', output)
    assert match is not None
    result = match.groupdict()
    assert result["program"] == expected_program
    assert re.search(expected_version_pattern, result["version"]) is not None


@pytest.mark.django_db
def test_ffmpeg_extraction_event_detail_command_returns_ffmpeg_version() -> None:
    expected_program = "ffmpeg"
    expected_version_pattern = r"^ffmpeg version"
    filters = {
        "command_usage": "event_detail",
        "description": "Get event detail text for ffmpeg extraction",
    }
    command = FPCommand.active.get(**filters)

    _, output, _ = executeOrRun(command.script_type, command.command)

    match = re.search(r'program="(?P<program>.*?)"; version="(?P<version>.*?)"', output)
    assert match is not None
    result = match.groupdict()
    assert result["program"] == expected_program
    assert re.search(expected_version_pattern, result["version"]) is not None
