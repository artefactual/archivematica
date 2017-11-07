# -*- coding: UTF-8 -*-
import pytest

import executeOrRunSubProcess as execsub

"""Tests behaviour of capture_output when executing sub processes."""
def test_capture_output():
        # Test that stdout and stderr are captured by default
        ret, std_out, std_err = execsub.launchSubProcess(['ls' , '/tmp'])
        assert std_out is not '' or std_err is not ''
        # Test that stdout and stderr are not captured when disabled
        ret, std_out, std_err = execsub.launchSubProcess(['ls', '/tmp'],
                                                         capture_output=False)
        assert std_out is ''
        assert std_err is''
