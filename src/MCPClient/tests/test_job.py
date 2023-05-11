import os
from uuid import uuid4

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
from job import Job


TEXT = "‘你好‘"


def test_job_encoding():
    job = Job(name="somejob", uuid=str(uuid4()), args=["a", "b"])

    job.pyprint(TEXT)
    stdout = job.get_stdout()
    expected_stdout = f"{TEXT}\n"
    expected_output = TEXT + "\n"
    assert job.output == expected_output
    assert stdout == expected_stdout
    assert isinstance(job.output, str)
    assert isinstance(stdout, str)

    job.print_error(TEXT)
    stderr = job.get_stderr()
    expected_stderr = f"{TEXT}\n"
    expected_error = TEXT + "\n"
    assert job.error == expected_error
    assert stderr == expected_stderr
    assert isinstance(job.error, str)
    assert isinstance(stderr, str)

    job_dump = job.dump()
    assert job.UUID in job_dump
    assert stderr in job_dump
    assert stdout in job_dump
