import logging
import select
import socket
import threading
from unittest import mock

import gearman
import pytest
from gearman.protocol import GEARMAN_COMMAND_CAN_DO
from gearman.protocol import GEARMAN_COMMAND_PRE_SLEEP
from gearman.protocol import GEARMAN_COMMAND_RESET_ABILITIES
from gearman.protocol import GEARMAN_COMMAND_SET_CLIENT_ID

from archivematica.archivematicaCommon.gearman import ExponentialBackoff
from archivematica.archivematicaCommon.gearman import GearmanConnection
from archivematica.archivematicaCommon.gearman import GearmanWorker


class FakeSocket:
    def __init__(self) -> None:
        self.options = []
        self.timeouts = []
        self.closed = False

    def setsockopt(self, level, option, value) -> None:
        self.options.append((level, option, value))

    def settimeout(self, timeout) -> None:
        self.timeouts.append(timeout)

    def setblocking(self, blocking) -> None:
        pass

    def close(self) -> None:
        self.closed = True


def test_connection_uses_hostname_and_configures_each_new_socket(monkeypatch):
    first_socket = FakeSocket()
    second_socket = FakeSocket()
    create_connection = mock.Mock(side_effect=(first_socket, second_socket))
    monkeypatch.setattr(socket, "create_connection", create_connection)

    connection = GearmanConnection("gearman.service", 4730)
    connection.connect()
    connection.close()
    connection.connect()

    assert create_connection.call_args_list == [
        mock.call(
            ("gearman.service", 4730),
            timeout=GearmanConnection.connect_timeout,
        ),
        mock.call(
            ("gearman.service", 4730),
            timeout=GearmanConnection.connect_timeout,
        ),
    ]

    for created_socket in (first_socket, second_socket):
        assert (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1) in created_socket.options
        if hasattr(socket, "TCP_KEEPIDLE"):
            assert (
                socket.IPPROTO_TCP,
                socket.TCP_KEEPIDLE,
                GearmanConnection.keepalive_idle,
            ) in created_socket.options
        if hasattr(socket, "TCP_KEEPINTVL"):
            assert (
                socket.IPPROTO_TCP,
                socket.TCP_KEEPINTVL,
                GearmanConnection.keepalive_interval,
            ) in created_socket.options
        if hasattr(socket, "TCP_KEEPCNT"):
            assert (
                socket.IPPROTO_TCP,
                socket.TCP_KEEPCNT,
                GearmanConnection.keepalive_count,
            ) in created_socket.options
        assert created_socket.timeouts == [0.0]


def test_connection_detects_clean_tcp_close():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind(("127.0.0.1", 0))
    except PermissionError:
        listener.close()
        pytest.skip("local TCP listeners are unavailable in this sandbox")
    listener.listen()

    def accept_and_close() -> None:
        accepted_socket, _ = listener.accept()
        accepted_socket.close()

    server_thread = threading.Thread(target=accept_and_close)
    server_thread.start()
    connection = GearmanConnection(*listener.getsockname())

    try:
        connection.connect()
        server_thread.join(timeout=1)
        readable, _, _ = select.select([connection.gearman_socket], [], [], 1)

        assert readable == [connection.gearman_socket]
        with pytest.raises(gearman.errors.ConnectionError, match="remote disconnected"):
            connection.read_data_from_socket()
    finally:
        connection.close()
        listener.close()


def test_exponential_backoff_applies_jitter_cap_and_reset():
    backoff = ExponentialBackoff(
        initial_delay=1,
        maximum_delay=5,
        multiplier=2,
        jitter=0.2,
        random_uniform=lambda low, high: high,
    )

    assert [backoff.next_delay() for _ in range(5)] == [1.2, 2.4, 4.8, 5, 5]

    backoff.reset()

    assert backoff.next_delay() == 1.2


class FakeReconnectingWorker(GearmanWorker):
    def __init__(self, connection_results, work_results=()) -> None:
        self.connection_list = ["gearman.service:4730"]
        self.connection_results = iter(connection_results)
        self.work_results = iter(work_results)
        self.poll_timeouts = []

    def establish_worker_connections(self):
        result = next(self.connection_results)
        if isinstance(result, BaseException):
            raise result
        return result

    def work(self, poll_timeout=60.0):
        self.poll_timeouts.append(poll_timeout)
        result = next(self.work_results, None)
        if isinstance(result, BaseException):
            raise result
        return result


class RecordingEvent:
    def __init__(self, stop_after_waits=None) -> None:
        self.waits = []
        self.stop_after_waits = stop_after_waits

    def is_set(self) -> bool:
        return False

    def wait(self, timeout) -> bool:
        self.waits.append(timeout)
        return self.stop_after_waits == len(self.waits)


def test_worker_recovers_without_repeated_outage_logs(caplog):
    worker = FakeReconnectingWorker(([], [], [object()]))
    event = RecordingEvent()
    backoff = ExponentialBackoff(jitter=0)
    unavailable = mock.Mock()

    with caplog.at_level(logging.INFO):
        worker.work_with_reconnect(
            event,
            logging.getLogger("test"),
            backoff=backoff,
            on_connection_unavailable=unavailable,
        )

    assert event.waits == [1.0, 2.0]
    assert worker.poll_timeouts == [5.0]
    outage_records = [
        record
        for record in caplog.records
        if "connection unavailable" in record.message
    ]
    assert len(outage_records) == 1
    unavailable.assert_called_once_with()
    assert any("Reconnected to Gearman" in record.message for record in caplog.records)


def test_worker_reconnects_after_established_connection_closes(caplog):
    worker = FakeReconnectingWorker(
        ([object()], [object()]),
        (gearman.errors.ServerUnavailable("connection lost"), None),
    )
    event = RecordingEvent()

    with caplog.at_level(logging.INFO):
        worker.work_with_reconnect(
            event,
            logging.getLogger("test"),
            backoff=ExponentialBackoff(jitter=0),
        )

    assert event.waits == [1.0]
    assert worker.poll_timeouts == [5.0, 5.0]
    assert (
        sum("connection unavailable" in record.message for record in caplog.records)
        == 1
    )
    assert any("Reconnected to Gearman" in record.message for record in caplog.records)


def test_worker_backoff_is_interrupted_by_shutdown():
    worker = FakeReconnectingWorker(([],))
    event = RecordingEvent(stop_after_waits=1)

    worker.work_with_reconnect(
        event,
        logging.getLogger("test"),
        backoff=ExponentialBackoff(jitter=0),
    )

    assert event.waits == [1.0]


def test_worker_resets_backoff_after_stable_connection():
    worker = FakeReconnectingWorker(
        ([object()],),
        (gearman.errors.ServerUnavailable("connection lost"),),
    )
    event = RecordingEvent(stop_after_waits=1)
    backoff = ExponentialBackoff(jitter=0)
    backoff.next_delay()
    backoff.next_delay()
    monotonic = mock.Mock(side_effect=(0.0, 31.0))

    worker.work_with_reconnect(
        event,
        logging.getLogger("test"),
        backoff=backoff,
        monotonic=monotonic,
    )

    assert event.waits == [1.0]


def test_worker_does_not_contain_programming_errors():
    worker = FakeReconnectingWorker((ValueError("broken worker"),))

    with pytest.raises(ValueError, match="broken worker"):
        worker.work_with_reconnect(threading.Event(), logging.getLogger("test"))


def test_worker_does_not_contain_programming_errors_from_work_loop():
    worker = FakeReconnectingWorker(([object()],), (ValueError("broken job"),))

    with pytest.raises(ValueError, match="broken job"):
        worker.work_with_reconnect(threading.Event(), logging.getLogger("test"))


def test_worker_reregisters_id_and_all_abilities_on_new_connection():
    worker = GearmanWorker([])
    worker.set_client_id(b"worker-1")
    worker.register_task(b"ability-1", mock.Mock())
    worker.register_task(b"ability-2", mock.Mock())
    connection = mock.Mock()
    connection.connected = False
    connection.connect.side_effect = lambda: setattr(connection, "connected", True)
    connection.close.side_effect = lambda: setattr(connection, "connected", False)
    worker.connection_list = [connection]

    worker.establish_connection(connection)
    first_registration = list(connection.send_command.call_args_list)
    worker.handle_error(connection)
    connection.send_command.reset_mock()
    worker.establish_connection(connection)

    expected_registration = [
        mock.call(GEARMAN_COMMAND_SET_CLIENT_ID, {"client_id": b"worker-1"}),
        mock.call(GEARMAN_COMMAND_RESET_ABILITIES, {}),
        mock.call(GEARMAN_COMMAND_CAN_DO, {"task": b"ability-1"}),
        mock.call(GEARMAN_COMMAND_CAN_DO, {"task": b"ability-2"}),
        mock.call(GEARMAN_COMMAND_PRE_SLEEP, {}),
    ]
    assert first_registration == expected_registration
    assert connection.send_command.call_args_list == expected_registration
