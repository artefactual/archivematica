from typing import Callable
from typing import List

from client import gearman


class FakeConnection:
    def __init__(self, connected: bool, writable: bool) -> None:
        self.connected = connected
        self._writable = writable

    def writable(self) -> bool:
        return self._writable


def make_worker(
    connections: List[FakeConnection],
    readiness_callback: Callable[[], None],
) -> gearman.MCPGearmanWorker:
    worker = gearman.MCPGearmanWorker.__new__(gearman.MCPGearmanWorker)
    worker.connection_list = connections
    worker.readiness_callback = readiness_callback
    worker.ready_reported = False
    worker.shutdown_event = None
    worker.max_jobs_to_process = None
    worker.jobs_processed_count = 0
    return worker


def test_after_poll_reports_ready_after_startup_commands_are_flushed() -> None:
    readiness_reports = []
    worker = make_worker(
        [FakeConnection(connected=True, writable=False)],
        lambda: readiness_reports.append(True),
    )

    assert worker.after_poll(any_activity=True) is True

    assert readiness_reports == [True]
    assert worker.ready_reported is True


def test_after_poll_waits_until_connected_worker_is_not_writable() -> None:
    readiness_reports = []
    worker = make_worker(
        [FakeConnection(connected=True, writable=True)],
        lambda: readiness_reports.append(True),
    )

    assert worker.after_poll(any_activity=True) is True

    assert readiness_reports == []
    assert worker.ready_reported is False


def test_after_poll_reports_ready_only_once() -> None:
    readiness_reports = []
    worker = make_worker(
        [FakeConnection(connected=True, writable=False)],
        lambda: readiness_reports.append(True),
    )

    assert worker.after_poll(any_activity=True) is True
    assert worker.after_poll(any_activity=True) is True

    assert readiness_reports == [True]
