import re
from typing import TypedDict

import pytest
from executeOrRunSubProcess import executeOrRun
from fpr.models import FPCommand


class QueryFilters(TypedDict):
    command_usage: str
    description: str


@pytest.mark.django_db
@pytest.mark.parametrize(
    "expected_program,expected_version_pattern,filters",
    [
        (
            "7z",
            # The event detail command extracts different lines depending on the 7z version.
            # Older versions report the version on a line starting with "p7zip Version"
            # while more recent versions use a line starting with "7-Zip".
            r"(^p7zip Version|^7-Zip)",
            {
                "command_usage": "event_detail",
                "description": "Get event detail text for 7z extraction",
            },
        ),
        (
            "convert",
            "^Version: ImageMagick",
            {
                "command_usage": "event_detail",
                "description": "convert event detail",
            },
        ),
        (
            "ffmpeg",
            r"^ffmpeg version",
            {
                "command_usage": "event_detail",
                "description": "Get event detail text for ffmpeg extraction",
            },
        ),
    ],
)
def test_event_detail_command_returns_tool_version(
    expected_program: str, expected_version_pattern: str, filters: QueryFilters
) -> None:
    command = FPCommand.active.get(**filters)

    _, output, _ = executeOrRun(command.script_type, command.command)

    match = re.search(r'program="(?P<program>.*?)"; version="(?P<version>.*?)"', output)
    assert match is not None
    result = match.groupdict()
    assert result["program"] == expected_program
    assert re.search(expected_version_pattern, result["version"]) is not None
