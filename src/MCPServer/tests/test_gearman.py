from __future__ import absolute_import, division, print_function, unicode_literals

import math
import uuid

import gearman
import pytest
import six
from six.moves import cPickle

from server.jobs import Job
from server.tasks import GearmanTaskBackend, Task


class MockJob(Job):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop("name", "")
        super(MockJob, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        pass


@pytest.fixture
def simple_job(request, mocker):
    return MockJob(mocker.Mock(), mocker.Mock(), mocker.Mock(), name="test_job_name")


@pytest.fixture
def simple_task(request):
    return Task(
        "a argument string",
        "/tmp/stdoutfile",
        "/tmp/stderrfile",
        {r"%relativeLocation%": "testfile"},
        wants_output=False,
    )


def format_gearman_request(tasks):
    request = {"tasks": {}}
    for task in tasks:
        task_uuid = str(task.uuid)
        request["tasks"][task_uuid] = {
            "uuid": task_uuid,
            "createdDate": task.start_timestamp.isoformat(str(" ")),
            "arguments": task.arguments,
            "wants_output": task.wants_output,
        }

    return cPickle.dumps(request, protocol=0)


def format_gearman_response(task_results):
    """Accepts task results as a tuple of (uuid, result_dict)."""
    response = {"task_results": {}}
    for task_uuid, task_data in task_results:
        task_uuid = str(task_uuid)
        response["task_results"][task_uuid] = task_data

    return cPickle.dumps(response, protocol=0)


def test_gearman_task_submission(simple_job, simple_task, mocker):
    # Mock to avoid db writes
    mocker.patch("server.tasks.backends.gearman_backend.Task.bulk_log")
    mocker.patch.object(GearmanTaskBackend, "TASK_BATCH_SIZE", 1)
    mock_client = mocker.patch("server.tasks.backends.gearman_backend.MCPGearmanClient")

    backend = GearmanTaskBackend()
    backend.submit_task(simple_job, simple_task)

    task_data = format_gearman_request([simple_task])

    submit_job_kwargs = mock_client.return_value.submit_job.call_args[1]

    assert submit_job_kwargs["task"] == six.ensure_binary(simple_job.name)
    # Comparing pickled strings is fragile, so compare the python version
    assert cPickle.loads(submit_job_kwargs["data"]) == cPickle.loads(task_data)
    try:
        uuid.UUID(six.ensure_text(submit_job_kwargs["unique"]))
    except ValueError:
        pytest.fail("Expected unique to be a valid UUID.")
    assert submit_job_kwargs["wait_until_complete"] is False
    assert submit_job_kwargs["background"] is False
    assert submit_job_kwargs["max_retries"] == 0


def test_gearman_task_result_success(simple_job, simple_task, mocker):
    # Mock to avoid db writes
    mocker.patch("server.tasks.backends.gearman_backend.Task.bulk_log")

    mock_client = mocker.patch("server.tasks.backends.gearman_backend.MCPGearmanClient")
    backend = GearmanTaskBackend()

    mock_gearman_job = mocker.Mock()
    job_request = gearman.job.GearmanJobRequest(
        mock_gearman_job, background=True, max_attempts=0
    )

    def mock_jobs_completed(*args):
        job_request.state = gearman.JOB_COMPLETE
        job_request.result = format_gearman_response(
            [
                (
                    simple_task.uuid,
                    {
                        "exitCode": 0,
                        "stdout": "stdout example",
                        "stderr": "stderr example",
                    },
                )
            ]
        )

        return [job_request]

    mock_client.return_value.submit_job.return_value = job_request
    mock_client.return_value.wait_until_any_job_completed.side_effect = (
        mock_jobs_completed
    )

    backend.submit_task(simple_job, simple_task)
    results = list(backend.wait_for_results(simple_job))

    assert len(results) == 1

    mock_client.return_value.submit_job.assert_called_once()
    mock_client.return_value.wait_until_any_job_completed.assert_called_once()

    task_result = results[0]
    assert task_result.exit_code == 0
    assert task_result.stdout == "stdout example"
    assert task_result.stderr == "stderr example"
    assert task_result.done is True


def test_gearman_task_result_error(simple_job, simple_task, mocker):
    # Mock to avoid db writes
    mocker.patch("server.tasks.backends.gearman_backend.Task.bulk_log")

    mock_client = mocker.patch("server.tasks.backends.gearman_backend.MCPGearmanClient")
    backend = GearmanTaskBackend()

    mock_gearman_job = mocker.Mock()
    job_request = gearman.job.GearmanJobRequest(
        mock_gearman_job, background=True, max_attempts=0
    )

    def mock_jobs_completed(*args):
        job_request.state = gearman.JOB_FAILED
        job_request.exception = cPickle.dumps(Exception("Error!"), protocol=0)

        return [job_request]

    mock_client.return_value.submit_job.return_value = job_request
    mock_client.return_value.wait_until_any_job_completed.side_effect = (
        mock_jobs_completed
    )

    backend.submit_task(simple_job, simple_task)
    results = list(backend.wait_for_results(simple_job))

    assert len(results) == 1

    mock_client.return_value.submit_job.assert_called_once()
    mock_client.return_value.wait_until_any_job_completed.assert_called_once()

    task_result = results[0]
    assert task_result.exit_code == 1
    assert task_result.done is True


@pytest.mark.parametrize(
    "reverse_result_order", (False, True), ids=["regular", "reversed"]
)
def test_gearman_multiple_batches(
    simple_job, simple_task, mocker, reverse_result_order
):
    # Mock to avoid db writes
    mocker.patch("server.tasks.backends.gearman_backend.Task.bulk_log")
    mocker.patch.object(GearmanTaskBackend, "TASK_BATCH_SIZE", 2)
    mock_client = mocker.patch("server.tasks.backends.gearman_backend.MCPGearmanClient")

    tasks = []
    for i in range(5):
        task = Task(
            "a argument string {}".format(i),
            "/tmp/stdoutfile",
            "/tmp/stderrfile",
            {r"%relativeLocation%": "testfile"},
            wants_output=False,
        )
        tasks.append(task)

    backend = GearmanTaskBackend()

    job_requests = []
    for i in range(3):
        mock_gearman_job = mocker.Mock()
        job_request = gearman.job.GearmanJobRequest(
            mock_gearman_job, background=True, max_attempts=0
        )
        job_requests.append(job_request)

    def mock_get_job_statuses(*args):
        """Complete one batch per call, either in regular or reverse order."""
        status_requests = list(job_requests)
        if reverse_result_order:
            status_requests = reversed(status_requests)
            task_batches = [tasks[4:], tasks[2:4], tasks[:2]]
        else:
            task_batches = [tasks[:2], tasks[2:4], tasks[4:]]

        for index, job_request in enumerate(status_requests):
            if job_request.state != gearman.JOB_COMPLETE:
                job_request.state = gearman.JOB_COMPLETE
                job_request.result = format_gearman_response(
                    [
                        (
                            task.uuid,
                            {
                                "exitCode": 0,
                                "stdout": "stdout example {}".format(index),
                                "stderr": "stderr example {}".format(index),
                            },
                        )
                        for task in task_batches[index]
                    ]
                )
                break

        return job_requests

    mock_client.return_value.submit_job.side_effect = job_requests
    mock_client.return_value.wait_until_any_job_completed.side_effect = (
        mock_get_job_statuses
    )

    for task in tasks:
        backend.submit_task(simple_job, task)
    results = list(backend.wait_for_results(simple_job))

    expected_batch_count = int(math.ceil(5 / backend.TASK_BATCH_SIZE))
    expected_first_result = tasks[-1] if reverse_result_order else tasks[0]

    assert len(results) == 5
    assert results[0] is expected_first_result
    assert mock_client.return_value.submit_job.call_count == expected_batch_count
    assert mock_client.return_value.wait_until_any_job_completed.call_count == len(
        job_requests
    )
