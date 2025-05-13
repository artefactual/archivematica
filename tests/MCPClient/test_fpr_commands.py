import re
from typing import TypedDict

import pytest

from archivematica.archivematicaCommon.executeOrRunSubProcess import executeOrRun
from archivematica.dashboard.fpr.models import FPCommand


class QueryFilters(TypedDict):
    command_usage: str
    description: str


class EventDetailResult(TypedDict):
    programs: list[str]
    version: str


@pytest.mark.django_db
@pytest.mark.parametrize(
    "expected_programs,expected_version_pattern,cmd,filters",
    [
        (
            ["7z"],
            # The event detail command extracts different lines depending on the 7z version.
            # Older versions report the version on a line starting with "p7zip Version"
            # while more recent versions use a line starting with "7-Zip".
            r"(^p7zip Version|^7-Zip)",
            'echo program=\\"7z\\"\\; version=\\"`7z | awk \'NR==3 && /^p7zip Version/ {print; exit} NR==2 {line2=$0} NR==3 {print line2 $0}\'`\\"',
            {
                "command_usage": "event_detail",
                "description": "Get event detail text for 7z extraction",
            },
        ),
        (
            ["convert"],
            "^Version: ImageMagick",
            'echo program=\\"convert\\"\\; version=\\"`convert -version | grep Version:`\\"',
            {
                "command_usage": "event_detail",
                "description": "convert event detail",
            },
        ),
        (
            ["ffmpeg"],
            r"^ffmpeg version",
            'echo program=\\"ffmpeg\\"\\; version=\\"`ffmpeg 2>&1 | grep --ignore-case "FFmpeg version"`\\"',
            {
                "command_usage": "event_detail",
                "description": "Get event detail text for ffmpeg extraction",
            },
        ),
        (
            ["ps2pdf", "Ghostscript"],
            r"^\d+\.\d+\.\d+",
            'echo program=\\"ps2pdf\\"\\; program=\\"Ghostscript\\"\\; version=\\"`gs --version`\\" ',
            {
                "command_usage": "event_detail",
                "description": "ps2pdf event detail",
            },
        ),
        (
            ["Ghostscript"],
            r"^\d+\.\d+\.\d+",
            'echo program=\\"Ghostscript\\"\\; version=\\"`gs --version`\\" ',
            {
                "command_usage": "event_detail",
                "description": "Ghostscript event detail",
            },
        ),
        (
            ["inkscape"],
            r"^Inkscape",
            'echo program=\\"inkscape\\"\\; version=\\"`inkscape -V`\\" ',
            {
                "command_usage": "event_detail",
                "description": "inkscape event detail",
            },
        ),
        pytest.param(
            ["unrar-nonfree"],
            "^UNRAR",
            'echo program=\\"unrar-nonfree\\"\\; version=\\"`unrar-nonfree | grep \'UNRAR\'`\\"',
            {
                "command_usage": "event_detail",
                "description": "Get event detail text for unrar extraction",
            },
            marks=pytest.mark.skip(
                reason="Skipping because unrar-nonfree is not installed by default in Archivematica"
            ),
        ),
        (
            ["readpst"],
            r"^ReadPST / LibPST",
            'echo program=\\"readpst\\"\\; version=\\"`readpst -V`\\"',
            {
                "command_usage": "event_detail",
                "description": "readpst event detail",
            },
        ),
    ],
    ids=[
        "7z",
        "convert",
        "ffmpeg",
        "ps2pdf",
        "Ghostscript",
        "inkscape",
        "unrar-nonfree",
        "readpst",
    ],
)
def test_event_detail_command_returns_tool_version(
    expected_programs: list[str],
    expected_version_pattern: str,
    cmd: str,
    filters: QueryFilters,
) -> None:
    command, _ = FPCommand.active.get_or_create(
        script_type="bashScript", command=cmd, **filters
    )

    _, output, _ = executeOrRun(command.script_type, command.command)

    result: EventDetailResult = {"programs": [], "version": ""}

    for match in re.finditer(
        r'program="(?P<program>.*?)";|version="(?P<version>.*?)"', output
    ):
        program = match.group("program")
        version = match.group("version")
        if program is not None:
            result["programs"].append(program)
        if version is not None:
            result["version"] = version

    assert result["programs"] == expected_programs
    assert re.search(expected_version_pattern, result["version"]) is not None


@pytest.mark.django_db
def test_mbox_event_detail_command_returns_tool_path() -> None:
    expected_detail_pattern = r"^/usr/lib/archivematica/transcoder/transcoderScripts/ "
    filters = {
        "command_usage": "event_detail",
        "description": "Transcoding maildir to mbox event detail",
    }
    command, _ = FPCommand.active.get_or_create(
        script_type="command",
        command='echo "/usr/lib/archivematica/transcoder/transcoderScripts/" "%fileFullName%" "%outputDirectory%%prefix%%fileName%%postfix%.mbox"',
        **filters,
    )

    _, output, _ = executeOrRun(command.script_type, command.command)

    assert re.search(expected_detail_pattern, output) is not None
