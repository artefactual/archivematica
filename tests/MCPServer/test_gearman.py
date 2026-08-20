import math
import threading
import uuid
from unittest import mock

import gearman
import pytest
from django.utils import timezone
from gearman.errors import ExceededConnectionAttempts
from gearman.errors import ServerUnavailable
from gearman.job import GearmanJob
from gearman.job import GearmanJobRequest

from archivematica.dashboard.main import models
from archivematica.MCPServer.server import metrics
from archivematica.MCPServer.server.jobs import DirectoryClientScriptJob
from archivematica.MCPServer.server.jobs import Job
from archivematica.MCPServer.server.tasks import GearmanTaskBackend
from archivematica.MCPServer.server.tasks import Task
from archivematica.MCPServer.server.tasks import TaskBackend
from archivematica.MCPServer.server.tasks.backends import backend_local
from archivematica.MCPServer.server.tasks.backends import get_task_backend
from archivematica.MCPServer.server.tasks.backends import invalidate_task_backends
from archivematica.MCPServer.server.tasks.backends import reset_task_backend
from archivematica.MCPServer.server.tasks.backends.gearman_backend import (
    GearmanTaskBatch,
)
from archivematica.MCPServer.server.tasks.backends.gearman_backend import (
    MCPGearmanClient,
)


class MockJob(Job):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop("name", "")
        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        pass


@pytest.fixture
def simple_job(request):
    return MockJob(mock.Mock(), mock.Mock(), mock.Mock(), name="test_job_name")


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
            "createdDate": task.start_timestamp,
            "arguments": task.arguments,
            "wants_output": task.wants_output,
        }

    return request


def format_gearman_response(task_results):
    """Accepts task results as a tuple of (uuid, result_dict)."""
    response = {"task_results": {}}
    for task_uuid, task_data in task_results:
        task_uuid = str(task_uuid)
        response["task_results"][task_uuid] = task_data

    return response


def test_ambiguous_pre_acknowledgement_loss_is_not_replayed():
    client = MCPGearmanClient([])
    request = GearmanJobRequest(
        GearmanJob(
            connection=mock.Mock(),
            handle=None,
            task=b"non-idempotent-task",
            unique=b"unique-task",
            data={},
        ),
        max_attempts=1,
    )
    # This is python-gearman's state after it queued one submission and then
    # lost the connection before receiving JOB_CREATED.
    request.connection_attempts = 1
    request.state = gearman.JOB_UNKNOWN

    with pytest.raises(ExceededConnectionAttempts):
        client.send_job_request(request)

    assert request.connection_attempts == 1


def test_post_acknowledgement_loss_is_not_replayed():
    client = MCPGearmanClient([])
    request = GearmanJobRequest(
        GearmanJob(
            connection=mock.Mock(),
            handle=b"H:server:1",
            task=b"non-idempotent-task",
            unique=b"unique-task",
            data={},
        )
    )
    request.state = gearman.JOB_CREATED
    client.poll_connections_until_stopped = mock.Mock(
        side_effect=ServerUnavailable("connection lost")
    )
    client.send_job_request = mock.Mock()

    with pytest.raises(ServerUnavailable):
        client.wait_until_jobs_completed([request])

    client.send_job_request.assert_not_called()


@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.MCPGearmanClient"
)
@mock.patch(
    "archivematica.MCPServer.server.tasks.GearmanTaskBackend.TASK_BATCH_SIZE", 1
)
@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.Task.bulk_log"
)
def test_gearman_task_submission(bulk_log, mock_client, simple_job, simple_task):
    backend = GearmanTaskBackend()
    backend.submit_task(simple_job, simple_task)

    task_data = format_gearman_request([simple_task])

    submit_job_kwargs = mock_client.return_value.submit_job.call_args[1]

    assert submit_job_kwargs["task"] == simple_job.name.encode()
    assert submit_job_kwargs["data"] == task_data
    try:
        uuid.UUID(submit_job_kwargs["unique"].decode())
    except ValueError:
        pytest.fail("Expected unique to be a valid UUID.")
    assert submit_job_kwargs["wait_until_complete"] is False
    assert submit_job_kwargs["background"] is False
    assert submit_job_kwargs["max_retries"] == GearmanTaskBackend.MAX_RETRIES


@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.MCPGearmanClient"
)
@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.Task.bulk_log"
)
def test_gearman_task_result_success(bulk_log, mock_client, simple_job, simple_task):
    backend = GearmanTaskBackend()

    mock_gearman_job = mock.Mock()
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


@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.MCPGearmanClient"
)
@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.Task.bulk_log"
)
@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.Task.bulk_mark_failed"
)
def test_gearman_task_result_error(
    bulk_mark_failed, bulk_log, mock_client, simple_job, simple_task
):
    backend = GearmanTaskBackend()

    mock_gearman_job = mock.Mock()
    job_request = gearman.job.GearmanJobRequest(
        mock_gearman_job, background=True, max_attempts=0
    )

    def mock_jobs_completed(*args):
        job_request.state = gearman.JOB_FAILED
        job_request.exception = Exception("Error!")

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
    bulk_mark_failed.assert_called_once()
    assert bulk_mark_failed.call_args.args[0] == [simple_task]
    assert "Gearman task batch" in bulk_mark_failed.call_args.args[1]
    assert "Error!" in bulk_mark_failed.call_args.args[1]


@pytest.mark.django_db(transaction=True)
def test_bulk_mark_failed_persists_task_failure(simple_task):
    job = models.Job.objects.create(
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_FAILED,
    )
    models.Task.objects.create(
        taskuuid=str(simple_task.uuid),
        job=job,
        createdtime=simple_task.start_timestamp,
        filename="testfile",
        execution="retrievetransfersource_v0.0",
        arguments=simple_task.arguments,
    )

    Task.bulk_mark_failed([simple_task], "Gearman task batch failed to execute.")

    task = models.Task.objects.get(taskuuid=simple_task.uuid)
    assert task.exitcode == 1
    assert task.stderror == "Gearman task batch failed to execute."
    assert task.endtime is not None
    assert simple_task.exit_code == 1
    assert simple_task.stderr == "Gearman task batch failed to execute."
    assert simple_task.finished_timestamp == task.endtime
    assert simple_task.done is True


@pytest.mark.parametrize(
    "reverse_result_order", (False, True), ids=["regular", "reversed"]
)
@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.MCPGearmanClient"
)
@mock.patch.object(GearmanTaskBackend, "TASK_BATCH_SIZE", 2)
@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.Task.bulk_log"
)
def test_gearman_multiple_batches(
    bulk_log, mock_client, simple_job, simple_task, reverse_result_order
):
    tasks = []
    for i in range(5):
        task = Task(
            f"a argument string {i}",
            "/tmp/stdoutfile",
            "/tmp/stderrfile",
            {r"%relativeLocation%": "testfile"},
            wants_output=False,
        )
        tasks.append(task)

    backend = GearmanTaskBackend()

    job_requests = []
    for _ in range(3):
        mock_gearman_job = mock.Mock()
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
                                "stdout": f"stdout example {index}",
                                "stderr": f"stderr example {index}",
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


@mock.patch(
    "archivematica.MCPServer.server.tasks.backends.gearman_backend.MCPGearmanClient"
)
def test_gearman_backend_shutdown_clears_state_and_reconciles_metrics(mock_client):
    backend = GearmanTaskBackend()
    unsent_batch = GearmanTaskBatch()
    unsent_batch.tasks.append(mock.Mock())
    empty_batch = GearmanTaskBatch()
    active_batch = GearmanTaskBatch()
    collected_batch = GearmanTaskBatch()
    collected_batch.collected = True
    backend.current_task_batches = {
        uuid.uuid4(): unsent_batch,
        uuid.uuid4(): empty_batch,
    }
    backend.pending_gearman_jobs = {
        uuid.uuid4(): [active_batch, collected_batch],
    }

    with (
        mock.patch.object(metrics.gearman_pending_jobs_gauge, "dec") as pending_dec,
        mock.patch.object(metrics.gearman_active_jobs_gauge, "dec") as active_dec,
    ):
        backend.shutdown()

    mock_client.return_value.shutdown.assert_called_once_with()
    pending_dec.assert_called_once_with(1)
    active_dec.assert_called_once_with(1)
    assert backend.current_task_batches == {}
    assert backend.pending_gearman_jobs == {}


def test_reset_task_backend_replaces_the_thread_local_backend():
    first_backend = mock.Mock(spec=TaskBackend)
    second_backend = mock.Mock(spec=TaskBackend)
    if hasattr(backend_local, "task_backend"):
        del backend_local.task_backend

    try:
        with mock.patch(
            "archivematica.MCPServer.server.tasks.backends.GearmanTaskBackend",
            side_effect=(first_backend, second_backend),
        ):
            assert get_task_backend() is first_backend
            assert get_task_backend() is first_backend

            reset_task_backend()

            first_backend.shutdown.assert_called_once_with()
            assert get_task_backend() is second_backend
    finally:
        if hasattr(backend_local, "task_backend"):
            del backend_local.task_backend


def test_invalidation_replaces_backends_owned_by_all_executor_threads():
    ready = threading.Barrier(3)
    invalidated = threading.Barrier(3)
    results = []

    def use_backend_across_invalidation():
        first = get_task_backend()
        ready.wait()
        invalidated.wait()
        second = get_task_backend()
        results.append((first, second))

    with mock.patch(
        "archivematica.MCPServer.server.tasks.backends.GearmanTaskBackend",
        side_effect=lambda: mock.Mock(spec=TaskBackend),
    ):
        threads = [
            threading.Thread(target=use_backend_across_invalidation) for _ in range(2)
        ]
        for thread in threads:
            thread.start()

        ready.wait()
        invalidate_task_backends()
        invalidated.wait()

        for thread in threads:
            thread.join(timeout=1)

    assert len(results) == 2
    for first, second in results:
        assert first is not second
        first.shutdown.assert_called_once_with()


def test_reset_task_backend_forgets_backend_when_shutdown_fails():
    backend = mock.Mock(spec=TaskBackend)
    backend.shutdown.side_effect = RuntimeError("shutdown failed")
    backend_local.task_backend = backend

    with pytest.raises(RuntimeError, match="shutdown failed"):
        reset_task_backend()

    assert not hasattr(backend_local, "task_backend")


def test_client_script_job_resets_backend_without_masking_original_error(caplog):
    package = mock.Mock()
    package.uuid = uuid.uuid4()
    package.get_replacement_mapping.return_value = {
        r"%relativeLocation%": "/tmp/testfile"
    }
    link = mock.Mock()
    link.id = uuid.uuid4()
    link.get_label.side_effect = lambda name, language: {
        "description": "A failing client job",
        "group": "Testing",
    }[name]
    link.config = {
        "arguments": '"%relativeLocation%"',
        "execute": "test_v0",
    }
    job_chain = mock.Mock()
    job_chain.context = {}
    job = DirectoryClientScriptJob(job_chain, link, package)
    backend = mock.Mock(spec=TaskBackend)
    backend.submit_task.side_effect = KeyError("unknown Gearman job handle")

    with (
        mock.patch.object(job, "save_to_db"),
        mock.patch(
            "archivematica.MCPServer.server.jobs.client.get_task_backend",
            return_value=backend,
        ),
        mock.patch(
            "archivematica.MCPServer.server.jobs.client.reset_task_backend",
            side_effect=RuntimeError("reset failed"),
        ) as reset_backend,
    ):
        with pytest.raises(KeyError, match="unknown Gearman job handle"):
            job.run()

    reset_backend.assert_called_once_with()
    assert any(
        record.message.startswith("Unable to reset task backend")
        for record in caplog.records
    )
