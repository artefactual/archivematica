# -*- coding: UTF-8 -*-

import shlex

import executeOrRunSubProcess as execsub


def test_capture_output():
    """Tests behaviour of capture_output when executing sub processes."""

    # Test that stdout and stderr are not captured by default
    ret, std_out, std_err = execsub.launchSubProcess(['ls', '/tmp'])
    assert std_out is ''
    assert std_err is ''

    # Test that stdout and stderr are captured when `capture_output` is
    # enabled.
    ret, std_out, std_err = execsub.launchSubProcess(
        ['ls', '/tmp'], capture_output=True)
    assert std_out is not '' or std_err is not ''

    # Test that stdout and stderr are not captured when `capture_output` is
    # not enabled.
    ret, std_out, std_err = execsub.launchSubProcess(
        ['ls', '/tmp'], capture_output=False)
    assert std_out is ''
    assert std_err is ''

    # Test that when `capture_output` is `False`, then stdout is never returned
    # and stderr is only returned when the exit code is non-zero.
    cmd1 = 'sh -c \'>&2 echo "error"; echo "out"; exit 1\''
    cmd0 = 'sh -c \'>&2 echo "error"; echo "out"; exit 0\''

    ret, std_out, std_err = execsub.launchSubProcess(
        shlex.split(cmd1), capture_output=False)
    assert std_out.strip() is ''
    assert std_err.strip() == 'error'

    ret, std_out, std_err = execsub.launchSubProcess(
        shlex.split(cmd0), capture_output=False)
    assert std_out.strip() is ''
    assert std_err.strip() == ''

    ret, std_out, std_err = execsub.launchSubProcess(
        shlex.split(cmd1), capture_output=True)
    assert std_out.strip() == 'out'
    assert std_err.strip() == 'error'

    ret, std_out, std_err = execsub.launchSubProcess(
        shlex.split(cmd0), capture_output=True)
    assert std_out.strip() == 'out'
    assert std_err.strip() == 'error'
