# -*- coding: UTF-8 -*-

import executeOrRunSubProcess as execsub


def test_capture_output():
    """Tests behaviour of capture_output when executing sub processes."""

    # Test that stdout and stderr are not captured by default
    ret, std_out, std_err = execsub.launchSubProcess(['ls', '/tmp'])
    assert std_out is ''
    assert std_err is''

    # Test that stdout and stderr are captured when `capture_output` is
    # enabled.
    ret, std_out, std_err = execsub.launchSubProcess(
        ['ls', '/tmp'], capture_output=True)
    assert std_out is not '' or std_err is not ''
