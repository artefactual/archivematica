import shlex
import tempfile
from unittest.mock import ANY
from unittest.mock import patch

import executeOrRunSubProcess as execsub
import pytest


def test_capture_output():
    """Tests behaviour of capture_output when executing sub processes."""

    # Test that stdout and stderr are not captured by default
    ret, std_out, std_err = execsub.launchSubProcess(["ls", "/tmp"])
    assert std_out == ""
    assert std_err == ""

    # Test that stdout and stderr are captured when `capture_output` is
    # enabled.
    ret, std_out, std_err = execsub.launchSubProcess(
        ["ls", "/tmp"], capture_output=True
    )
    assert std_out != "" or std_err != ""

    # Test that stdout and stderr are not captured when `capture_output` is
    # not enabled.
    ret, std_out, std_err = execsub.launchSubProcess(
        ["ls", "/tmp"], capture_output=False
    )
    assert std_out == ""
    assert std_err == ""

    # Test that when `capture_output` is `False`, then stdout is never returned
    # and stderr is only returned when the exit code is non-zero.
    cmd1 = 'sh -c \'>&2 echo "error"; echo "out"; exit 1\''
    cmd0 = 'sh -c \'>&2 echo "error"; echo "out"; exit 0\''

    ret, std_out, std_err = execsub.launchSubProcess(
        shlex.split(cmd1), capture_output=False
    )
    assert std_out.strip() == ""
    assert std_err.strip() == "error"

    ret, std_out, std_err = execsub.launchSubProcess(
        shlex.split(cmd0), capture_output=False
    )
    assert std_out.strip() == ""
    assert std_err.strip() == ""

    ret, std_out, std_err = execsub.launchSubProcess(
        shlex.split(cmd1), capture_output=True
    )
    assert std_out.strip() == "out"
    assert std_err.strip() == "error"

    ret, std_out, std_err = execsub.launchSubProcess(
        shlex.split(cmd0), capture_output=True
    )
    assert std_out.strip() == "out"
    assert std_err.strip() == "error"


@pytest.fixture
def temp_path(tmp_path):
    """Creates custom temp path, yields the value, and resets to original value."""

    original_tempdir = tempfile.tempdir
    tempfile.tempdir = tmp_path.as_posix()

    yield tmp_path.as_posix()

    tempfile.tempdir = original_tempdir


@patch("executeOrRunSubProcess.launchSubProcess")
def test_createAndRunScript_creates_tmpfile_in_custom_dir(launchSubProcess, temp_path):
    """Tests execution of launchSubProcess when executing createAndRunScript."""

    script_content = "#!/bin/bash\necho 'Script output'\nexit 0"

    execsub.createAndRunScript(script_content)

    launchSubProcess.assert_called_once_with(
        ANY,
        stdIn="",
        printing=True,
        env_updates={},
        capture_output=True,
    )
    args, _ = launchSubProcess.call_args
    assert args[0][0].startswith(temp_path)
