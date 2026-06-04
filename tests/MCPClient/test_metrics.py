import logging
import os
import pathlib
import queue
import subprocess
import sys
import textwrap
import time

from prometheus_client import generate_latest

from archivematica.archivematicaCommon import common_metrics
from archivematica.MCPClient.client import metrics


class FakeQueue:
    def __init__(self) -> None:
        self.items: list[object] = []

    def put_nowait(self, item: object) -> None:
        self.items.append(item)


def test_worker_metric_calls_are_queued(monkeypatch) -> None:
    fake_queue = FakeQueue()
    monkeypatch.setattr(metrics.settings, "PROMETHEUS_ENABLED", True)
    monkeypatch.setattr(metrics.time, "time", lambda: 123.0)

    metrics.configure_event_queue(fake_queue)
    try:
        metrics.job_completed("copy_v0.0")
    finally:
        metrics.configure_event_queue(None)

    assert fake_queue.items == [
        metrics.MetricEvent(
            "job_counter",
            "inc",
            (("script_name", "copy_v0.0"),),
            1.0,
        ),
        metrics.MetricEvent(
            "job_processed_timestamp",
            "set_max",
            (("script_name", "copy_v0.0"),),
            123.0,
        ),
    ]


def test_metric_events_are_applied_to_parent_registry(monkeypatch) -> None:
    monkeypatch.setattr(metrics.settings, "PROMETHEUS_ENABLED", True)

    metrics.apply_event(
        metrics.MetricEvent(
            "job_counter",
            "inc",
            (("script_name", "event-test_v0.0"),),
            3.0,
        )
    )

    output = generate_latest(metrics.REGISTRY).decode()

    assert 'mcpclient_job_total{script_name="event-test_v0.0"} 3.0' in output


def test_timestamp_metric_events_keep_highest_timestamp() -> None:
    labels = (("script_name", "out-of-order-timestamp_v0.0"),)
    metrics.apply_event(
        metrics.MetricEvent("job_processed_timestamp", "set_max", labels, 200.0)
    )
    metrics.apply_event(
        metrics.MetricEvent("job_processed_timestamp", "set_max", labels, 100.0)
    )

    output = generate_latest(metrics.REGISTRY).decode()

    assert (
        'mcpclient_job_success_timestamp{script_name="out-of-order-timestamp_v0.0"} 200.0'
        in output
    )


def test_metric_listener_logs_apply_failures_and_continues(monkeypatch, caplog) -> None:
    event_queue: queue.Queue[metrics.MetricEvent] = queue.Queue()
    listener = metrics.EventListener(event_queue)
    bad_event = metrics.MetricEvent("job_counter", "inc", (), 1.0)
    good_event = metrics.MetricEvent(
        "job_counter",
        "inc",
        (("script_name", "after-bad-event_v0.0"),),
        1.0,
    )
    applied_events: list[metrics.MetricEvent] = []

    def fake_apply_event(event: metrics.MetricEvent) -> None:
        if event == bad_event:
            raise ValueError("bad metric event")
        applied_events.append(event)

    monkeypatch.setattr(metrics, "apply_event", fake_apply_event)
    caplog.set_level(logging.ERROR, logger=metrics.logger.name)

    processed_by_listener = False
    listener.start()
    try:
        event_queue.put_nowait(bad_event)
        event_queue.put_nowait(good_event)

        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if good_event in applied_events:
                processed_by_listener = True
                break
            time.sleep(0.01)
    finally:
        listener.stop()

    assert processed_by_listener
    assert "Failed to apply MCPClient metric event" in caplog.text


def test_transfer_completed_records_zero_size_for_empty_transfer(monkeypatch) -> None:
    class FakeTransfer:
        type = "Standard"

    class EmptyFileQuerySet:
        def count(self) -> int:
            return 0

        def aggregate(self, **kwargs: object) -> dict[str, object]:
            return {"total_size": None}

    fake_queue = FakeQueue()
    monkeypatch.setattr(metrics.settings, "PROMETHEUS_ENABLED", True)
    monkeypatch.setattr(
        metrics.Transfer.objects, "get", lambda **kwargs: FakeTransfer()
    )
    monkeypatch.setattr(
        metrics.File.objects, "filter", lambda **kwargs: EmptyFileQuerySet()
    )

    metrics.configure_event_queue(fake_queue)
    try:
        metrics.transfer_completed("empty-transfer")
    finally:
        metrics.configure_event_queue(None)

    assert (
        metrics.MetricEvent(
            "transfer_size_histogram",
            "observe",
            (("transfer_type", "Standard"),),
            0,
        )
        in fake_queue.items
    )


def test_metrics_import_resets_prometheus_multiprocess_mode(
    tmp_path: pathlib.Path,
) -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    pythonpath = [
        str(repo_root / "src"),
        str(repo_root / "src" / "archivematica" / "MCPClient"),
    ]

    env = os.environ.copy()
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    env["DJANGO_SETTINGS_MODULE"] = "settings.test"
    env["PROMETHEUS_MULTIPROC_DIR"] = str(tmp_path)

    code = textwrap.dedent(
        """
        import os

        from archivematica.archivematicaCommon import common_metrics
        from prometheus_client import values

        assert common_metrics.ss_api_time_counter
        assert values.ValueClass._multiprocess

        from archivematica.MCPClient.client import metrics

        assert os.environ.get("PROMETHEUS_MULTIPROC_DIR") is None
        assert not values.ValueClass._multiprocess
        metrics.job_completed("copy_v0.0")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr


def test_storage_service_api_timer_events_are_queued(monkeypatch) -> None:
    fake_queue = FakeQueue()
    times = iter([100.0, 102.5])
    monkeypatch.setattr(common_metrics.time, "time", lambda: next(times))

    metrics.configure_event_queue(fake_queue)
    try:
        with common_metrics.ss_api_timer(function="get_file_info"):
            pass
    finally:
        metrics.configure_event_queue(None)

    assert fake_queue.items == [
        metrics.MetricEvent(
            "ss_api_time_counter",
            "inc",
            (("function", "get_file_info"),),
            2.5,
        )
    ]


def test_storage_service_api_timer_events_are_exposed_in_mcpclient_registry() -> None:
    metrics.apply_event(
        metrics.MetricEvent(
            "ss_api_time_counter",
            "inc",
            (("function", "store_aip"),),
            1.25,
        )
    )

    output = generate_latest(metrics.REGISTRY).decode()

    assert "# TYPE common_ss_api_request_duration_seconds_total counter" in output
    assert (
        'common_ss_api_request_duration_seconds_total{function="store_aip"} 1.25'
        in output
    )


def test_registry_preserves_mcpclient_metric_contract(monkeypatch) -> None:
    monkeypatch.setattr(metrics.settings, "PROMETHEUS_DETAILED_METRICS", False)

    metrics.init_counter_labels()
    output = generate_latest(metrics.REGISTRY).decode()

    assert "python_info" not in output
    assert "process_cpu_seconds_total" not in output
    assert "_created" not in output

    expected_types = {
        "mcpclient_job_total": "counter",
        "mcpclient_job_success_timestamp": "gauge",
        "mcpclient_job_error_total": "counter",
        "mcpclient_job_error_timestamp": "gauge",
        "mcpclient_task_execution_time_seconds": "histogram",
        "mcpclient_transfer_started_total": "counter",
        "mcpclient_transfer_started_timestamp": "gauge",
        "mcpclient_transfer_completed_total": "counter",
        "mcpclient_transfer_completed_timestamp": "gauge",
        "mcpclient_transfer_error_total": "counter",
        "mcpclient_transfer_error_timestamp": "gauge",
        "mcpclient_transfer_files": "histogram",
        "mcpclient_transfer_size_bytes": "histogram",
        "mcpclient_sip_started_total": "counter",
        "mcpclient_sip_started_timestamp": "gauge",
        "mcpclient_sip_error_total": "counter",
        "mcpclient_sip_error_timestamp": "gauge",
        "mcpclient_aips_stored_total": "counter",
        "mcpclient_dips_stored_total": "counter",
        "mcpclient_aips_stored_timestamp": "gauge",
        "mcpclient_dips_stored_timestamp": "gauge",
        "mcpclient_aip_processing_seconds": "histogram",
        "mcpclient_dip_processing_seconds": "histogram",
        "mcpclient_aip_files_stored": "histogram",
        "mcpclient_dip_files_stored": "histogram",
        "mcpclient_aip_size_bytes": "histogram",
        "mcpclient_dip_size_bytes": "histogram",
        "mcpclient_aip_original_file_timestamps": "histogram",
        "common_ss_api_request_duration_seconds_total": "counter",
    }

    for metric_name, metric_type in expected_types.items():
        assert f"# TYPE {metric_name} {metric_type}" in output

    assert 'mcpclient_job_total{script_name="copy_v0.0"}' in output
    assert 'mcpclient_transfer_started_total{transfer_type="Standard"}' in output
    assert (
        'mcpclient_transfer_error_total{failure_type="fail",transfer_type="Standard"}'
    ) in output
    assert (
        'mcpclient_task_execution_time_seconds_bucket{le="2.0",script_name="copy_v0.0"}'
    ) in output
