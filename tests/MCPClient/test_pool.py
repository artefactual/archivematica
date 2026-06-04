import queue
from typing import Any

import pytest

from archivematica.MCPClient.client import pool


class FakeReadinessQueue:
    def __init__(self, messages: list[pool.WorkerReadyMessage]) -> None:
        self.messages = messages

    def get_nowait(self) -> pool.WorkerReadyMessage:
        try:
            return self.messages.pop(0)
        except IndexError:
            raise queue.Empty


class FakeWorker:
    exitcode = None

    def __init__(self, pid: int, alive: bool = True) -> None:
        self.pid = pid
        self.alive = alive
        self.terminated = False
        self.killed = False
        self.join_calls: list[Any] = []

    def is_alive(self) -> bool:
        return self.alive

    def terminate(self) -> None:
        self.terminated = True
        self.alive = False
        self.exitcode = -15

    def kill(self) -> None:
        self.killed = True
        self.alive = False
        self.exitcode = -9

    def join(self, timeout: float | None = None) -> None:
        self.join_calls.append(timeout)


def test_collect_worker_readiness_ignores_stale_worker_messages() -> None:
    worker_pool = pool.WorkerPool.__new__(pool.WorkerPool)
    worker_pool.workers = [FakeWorker(222)]
    worker_pool.worker_ready = {}
    worker_pool.worker_ready_at = {}
    worker_pool.worker_started_at = {0: 10.0}
    worker_pool.worker_state = {0: pool.WorkerState.STARTING}
    worker_pool.worker_readiness_queue = FakeReadinessQueue(
        [
            pool.WorkerReadyMessage(worker_index=0, process_id=111),
            pool.WorkerReadyMessage(worker_index=1, process_id=333),
            pool.WorkerReadyMessage(worker_index=0, process_id=222),
        ]
    )

    worker_pool._collect_worker_readiness()

    assert worker_pool.worker_ready == {0: 222}
    assert worker_pool.worker_state == {0: pool.WorkerState.READY}


def test_collect_worker_readiness_records_ready_timestamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker_pool = pool.WorkerPool.__new__(pool.WorkerPool)
    worker_pool.workers = [FakeWorker(222)]
    worker_pool.worker_ready = {}
    worker_pool.worker_ready_at = {}
    worker_pool.worker_started_at = {0: 10.0}
    worker_pool.worker_state = {0: pool.WorkerState.STARTING}
    worker_pool.worker_readiness_queue = FakeReadinessQueue(
        [pool.WorkerReadyMessage(worker_index=0, process_id=222)]
    )
    monkeypatch.setattr(pool.time, "monotonic", lambda: 12.5)

    worker_pool._collect_worker_readiness()

    assert worker_pool.worker_ready == {0: 222}
    assert worker_pool.worker_ready_at == {0: 12.5}
    assert worker_pool.worker_state == {0: pool.WorkerState.READY}


def test_restart_unready_workers_replaces_alive_workers_after_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = FakeWorker(123)
    replacement = FakeWorker(456)
    worker_pool = pool.WorkerPool.__new__(pool.WorkerPool)
    worker_pool.workers = [worker]
    worker_pool.worker_ready = {}
    worker_pool.worker_ready_at = {}
    worker_pool.worker_started_at = {0: 0.0}
    worker_pool.worker_state = {0: pool.WorkerState.STARTING}
    worker_pool.WORKER_STARTUP_TIMEOUT = 30.0
    worker_pool.WORKER_TERMINATE_TIMEOUT = 0.1
    worker_pool._start_worker = lambda index: replacement
    traceback_dump_requests: list[tuple[int, int]] = []
    worker_pool._dump_unready_worker_traceback = lambda index, worker: (
        traceback_dump_requests.append((index, worker.pid))
    )
    exited_worker_pids: list[int] = []
    monkeypatch.setattr(pool.time, "monotonic", lambda: 31.0)
    monkeypatch.setattr(pool.metrics, "worker_exit", exited_worker_pids.append)

    restarted = worker_pool._restart_unready_workers()

    assert restarted is True
    assert worker.terminated is True
    assert worker.killed is False
    assert worker.join_calls == [0.1]
    assert worker_pool.workers == [replacement]
    assert worker_pool.worker_state == {0: pool.WorkerState.UNREADY_TIMEOUT}
    assert traceback_dump_requests == [(0, 123)]
    assert exited_worker_pids == [123]


def test_restart_exited_workers_records_exited_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = FakeWorker(123, alive=False)
    worker.exitcode = 0
    replacement = FakeWorker(456)
    worker_pool = pool.WorkerPool.__new__(pool.WorkerPool)
    worker_pool.workers = [worker]
    worker_pool.worker_ready = {0: 123}
    worker_pool.worker_ready_at = {0: 12.0}
    worker_pool.worker_state = {0: pool.WorkerState.READY}
    worker_pool._start_worker = lambda index: replacement
    exited_worker_pids: list[int] = []
    monkeypatch.setattr(pool.metrics, "worker_exit", exited_worker_pids.append)

    restarted = worker_pool._restart_exited_workers()

    assert restarted is True
    assert worker.join_calls == [None]
    assert worker_pool.workers == [replacement]
    assert worker_pool.worker_ready == {}
    assert worker_pool.worker_ready_at == {}
    assert worker_pool.worker_state == {0: pool.WorkerState.EXITED}
    assert exited_worker_pids == [123]


def test_dump_unready_worker_traceback_requests_child_stack(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = FakeWorker(123)
    worker_pool = pool.WorkerPool.__new__(pool.WorkerPool)
    worker_pool.WORKER_TRACEBACK_DUMP_DELAY = 0.5
    kill_requests: list[tuple[int, int]] = []
    sleep_requests: list[float] = []
    monkeypatch.setattr(
        pool.os, "kill", lambda pid, sig: kill_requests.append((pid, sig))
    )
    monkeypatch.setattr(pool.time, "sleep", sleep_requests.append)

    worker_pool._dump_unready_worker_traceback(0, worker)

    assert kill_requests == [(123, pool.signal.SIGUSR1)]
    assert sleep_requests == [0.5]
