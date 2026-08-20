from typing import Any
from unittest import mock

import pytest

from archivematica.MCPClient.client import pool


class FakeProcess:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.daemon = False
        self.started = False

    def start(self) -> None:
        self.started = True


class FakeContext:
    def __init__(self) -> None:
        self.queues: list[object] = []
        self.events: list[object] = []
        self.processes: list[FakeProcess] = []

    def Queue(self, **kwargs: Any) -> object:
        queue = object()
        self.queues.append(queue)
        return queue

    def Event(self) -> object:
        event = object()
        self.events.append(event)
        return event

    def Process(self, **kwargs: Any) -> FakeProcess:
        process = FakeProcess(**kwargs)
        self.processes.append(process)
        return process


def test_worker_pool_uses_forkserver_context_for_shared_primitives(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_context = FakeContext()
    monkeypatch.setattr(pool, "MP_CONTEXT", fake_context)
    monkeypatch.setattr(pool.settings, "WORKERS", 1)
    monkeypatch.setattr(pool.settings, "CLIENT_MODULES_FILE", "clientModules.conf")
    monkeypatch.setattr(
        pool.loader, "load_job_modules", lambda path: {"copy_v0.0": None}
    )
    monkeypatch.setattr(pool.loader, "get_module_concurrency", lambda module: 1)

    worker_pool = pool.WorkerPool()

    assert worker_pool.log_queue is fake_context.queues[0]
    assert worker_pool.metrics_queue is fake_context.queues[1]
    assert worker_pool.shutdown_event is fake_context.events[0]

    worker = worker_pool._start_worker(0)
    fake_worker = fake_context.processes[0]

    assert worker is fake_worker
    assert fake_worker.started is True
    assert fake_worker.kwargs["target"] is pool.run_gearman_worker
    assert fake_worker.kwargs["args"] == (
        worker_pool.log_queue,
        worker_pool.metrics_queue,
        ["copy_v0.0"],
    )
    assert fake_worker.kwargs["kwargs"] == {
        "shutdown_event": worker_pool.shutdown_event
    }


@mock.patch("archivematica.MCPClient.client.pool.MCPGearmanWorker")
def test_worker_process_reconnects_without_returning_to_pool(gearman_worker):
    shutdown_event = mock.Mock()
    log_queue = mock.Mock()
    metrics_queue = mock.Mock()

    with (
        mock.patch.object(pool.logging, "getLogger", return_value=mock.Mock()),
        mock.patch.object(pool.logging.handlers, "QueueHandler"),
        mock.patch.object(pool.metrics, "configure_event_queue"),
        mock.patch.object(pool.db.connections, "close_all"),
        mock.patch.object(pool.settings, "GEARMAN_SERVER", "gearman.service:4730"),
        mock.patch.object(pool.settings, "MAX_TASKS_PER_CHILD", None),
    ):
        pool.run_gearman_worker(
            log_queue,
            metrics_queue,
            ["ability-1"],
            shutdown_event=shutdown_event,
        )

    gearman_worker.return_value.work_with_reconnect.assert_called_once_with(
        shutdown_event, mock.ANY
    )


@mock.patch("archivematica.MCPClient.client.pool.MCPGearmanWorker")
def test_direct_worker_process_gets_a_local_shutdown_event(gearman_worker):
    with (
        mock.patch.object(pool.logging, "getLogger", return_value=mock.Mock()),
        mock.patch.object(pool.logging.handlers, "QueueHandler"),
        mock.patch.object(pool.metrics, "configure_event_queue"),
        mock.patch.object(pool.db.connections, "close_all"),
        mock.patch.object(pool.settings, "GEARMAN_SERVER", "gearman.service:4730"),
        mock.patch.object(pool.settings, "MAX_TASKS_PER_CHILD", None),
    ):
        pool.run_gearman_worker(mock.Mock(), mock.Mock(), ["ability-1"])

    shutdown_event = gearman_worker.call_args.kwargs["shutdown_event"]
    assert shutdown_event is not None
    gearman_worker.return_value.work_with_reconnect.assert_called_once_with(
        shutdown_event, mock.ANY
    )
