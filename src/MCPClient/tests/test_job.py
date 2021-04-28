# -*- coding: utf-8 -*-
import os
import sys
from uuid import uuid4

import six

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
from job import Job


UNICODE = six.ensure_text("‘你好‘")
NON_ASCII_BYTES = six.ensure_binary("‘你好‘")


def test_job_encoding():
    job = Job(name="somejob", uuid=str(uuid4()), args=["a", "b"])

    job.pyprint(UNICODE)
    stdout = job.get_stdout()
    expected_stdout = u"{}\n".format(UNICODE)
    expected_output = six.ensure_binary(UNICODE + "\n")
    assert job.output == expected_output
    assert stdout == expected_stdout
    assert isinstance(job.output, six.binary_type)
    assert isinstance(stdout, six.text_type)

    job.print_error(NON_ASCII_BYTES)
    stderr = job.get_stderr()
    expected_stderr = u"{}\n".format(NON_ASCII_BYTES.decode("utf-8"))
    expected_error = NON_ASCII_BYTES + b"\n"
    assert job.error == expected_error
    assert stderr == expected_stderr
    assert isinstance(job.error, six.binary_type)
    assert isinstance(stderr, six.text_type)

    job_dump = job.dump()
    assert job.UUID in job_dump
    assert stderr in job_dump
    assert stdout in job_dump
