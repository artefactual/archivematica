# -*- coding: utf-8 -*-
import os
from uuid import uuid4

import six

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
from client.job import Job


UNICODE = six.ensure_text("‘你好‘")
NON_ASCII_BYTES = six.ensure_binary("‘你好‘")


def test_job_encoding():
    job = Job("somejob", str(uuid4()), ["a", "b"])

    job.pyprint(UNICODE)
    stdout = job.get_stdout()
    expected_stdout = "{}\n".format(UNICODE)
    assert stdout == expected_stdout
    assert isinstance(stdout, six.text_type)

    job.print_error(NON_ASCII_BYTES)
    stderr = job.get_stderr()
    expected_stderr = "{}\n".format(NON_ASCII_BYTES.decode("utf-8"))
    assert stderr == expected_stderr
    assert isinstance(stderr, six.text_type)
