from typing import Any

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

    def Queue(self) -> object:
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
    assert worker_pool.shutdown_event is fake_context.events[0]

    worker = worker_pool._start_worker(0)
    fake_worker = fake_context.processes[0]

    assert worker is fake_worker
    assert fake_worker.started is True
    assert fake_worker.kwargs["target"] is pool.run_gearman_worker
    assert fake_worker.kwargs["args"] == (
        worker_pool.log_queue,
        ["copy_v0.0"],
    )
    assert fake_worker.kwargs["kwargs"] == {
        "shutdown_event": worker_pool.shutdown_event
    }
