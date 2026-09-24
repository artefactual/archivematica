"""Expose MCPClient metrics via Prometheus.

MCPClient supervises short-lived worker processes while the parent process owns
a single Prometheus registry. Worker processes send compact :class:`MetricEvent`
messages over a multiprocessing queue, and the parent applies those events to
``REGISTRY``. This keeps metric state in one long-lived process while
preserving the public MCPClient metric names.
"""

import configparser
import datetime
import functools
import logging
import queue
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any
from typing import Callable
from typing import NamedTuple
from typing import Optional
from typing import Protocol
from typing import TypeVar
from typing import cast
from wsgiref.simple_server import WSGIServer

import django

django.setup()

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from prometheus_client import CollectorRegistry
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram
from prometheus_client import start_http_server

from archivematica.archivematicaCommon import common_metrics
from archivematica.archivematicaCommon.common_metrics import PACKAGE_FILE_COUNT_BUCKETS
from archivematica.archivematicaCommon.common_metrics import PACKAGE_SIZE_BUCKETS
from archivematica.archivematicaCommon.common_metrics import PROCESSING_TIME_BUCKETS
from archivematica.archivematicaCommon.common_metrics import TASK_DURATION_BUCKETS
from archivematica.dashboard.fpr.models import FormatVersion
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import FileFormatVersion
from archivematica.dashboard.main.models import Transfer

logger = logging.getLogger("archivematica.mcp.client.metrics")


class MetricQueue(Protocol):
    """Small protocol shared by multiprocessing and test queues.

    Workers only need non-blocking writes. The parent listener uses blocking
    reads while running and non-blocking reads during shutdown drain.
    """

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any: ...
    def get_nowait(self) -> Any: ...
    def put_nowait(self, item: Any) -> None: ...


class MetricEvent(NamedTuple):
    """A metric mutation sent from a worker to the parent process.

    ``collector`` is a key in ``_COLLECTORS`` rather than a metric name. The
    event represents an operation to replay on the parent-owned collector, not
    a Prometheus sample.
    """

    collector: str
    action: str
    labels: tuple[tuple[str, str], ...] = ()
    value: float = 1.0


# Dedicated registry served by MCPClient's /metrics endpoint. It intentionally
# excludes prometheus_client's default runtime/process collectors.
REGISTRY = CollectorRegistry()
_EVENT_QUEUE: Optional[MetricQueue] = None
_EVENT_QUEUE_LOCK = threading.RLock()
_CURRENT_SCRIPT_NAME: ContextVar[Optional[str]] = ContextVar(
    "mcpclient_script_name", default=None
)
_GAUGE_MAX_VALUES: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
_GAUGE_MAX_VALUES_LOCK = threading.RLock()
_QUEUE_WRITE_FAILURE_LOGGED = False
_QUEUE_WRITE_FAILURE_LOCK = threading.Lock()


job_counter = Counter(
    "mcpclient_job_total",
    "Number of jobs processed, labeled by script",
    ["script_name"],
    registry=REGISTRY,
)
job_processed_timestamp = Gauge(
    "mcpclient_job_success_timestamp",
    "Timestamp of most recent job processed, labeled by script",
    ["script_name"],
    registry=REGISTRY,
)
job_error_counter = Counter(
    "mcpclient_job_error_total",
    "Number of failures processing jobs, labeled by script",
    ["script_name"],
    registry=REGISTRY,
)
job_error_timestamp = Gauge(
    "mcpclient_job_error_timestamp",
    "Timestamp of most recent job failure, labeled by script",
    ["script_name"],
    registry=REGISTRY,
)

task_execution_time_histogram = Histogram(
    "mcpclient_task_execution_time_seconds",
    "Histogram of worker task execution times in seconds, labeled by script",
    ["script_name"],
    buckets=TASK_DURATION_BUCKETS,
    registry=REGISTRY,
)
database_transaction_duration_histogram = Histogram(
    "mcpclient_database_transaction_duration_seconds",
    "Duration of outer database transactions, labeled by client script",
    ["script_name"],
    buckets=(
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        300.0,
        900.0,
        3600.0,
        7200.0,
        14400.0,
        28800.0,
        float("inf"),
    ),
    registry=REGISTRY,
)

transfer_started_counter = Counter(
    "mcpclient_transfer_started_total",
    "Number of Transfers started, by transfer type",
    ["transfer_type"],
    registry=REGISTRY,
)
transfer_started_timestamp = Gauge(
    "mcpclient_transfer_started_timestamp",
    "Timestamp of most recent transfer started, by transfer type",
    ["transfer_type"],
    registry=REGISTRY,
)
transfer_completed_counter = Counter(
    "mcpclient_transfer_completed_total",
    "Number of Transfers completed, by transfer type",
    ["transfer_type"],
    registry=REGISTRY,
)
transfer_completed_timestamp = Gauge(
    "mcpclient_transfer_completed_timestamp",
    "Timestamp of most recent transfer completed, by transfer type",
    ["transfer_type"],
    registry=REGISTRY,
)
transfer_error_counter = Counter(
    "mcpclient_transfer_error_total",
    "Number of transfer failures, by transfer type, error type",
    ["transfer_type", "failure_type"],
    registry=REGISTRY,
)
transfer_error_timestamp = Gauge(
    "mcpclient_transfer_error_timestamp",
    "Timestamp of most recent transfer failure, by transfer type, error type",
    ["transfer_type", "failure_type"],
    registry=REGISTRY,
)
transfer_files_histogram = Histogram(
    "mcpclient_transfer_files",
    "Histogram of number of files included in transfers, by transfer type",
    ["transfer_type"],
    buckets=PACKAGE_FILE_COUNT_BUCKETS,
    registry=REGISTRY,
)
transfer_size_histogram = Histogram(
    "mcpclient_transfer_size_bytes",
    "Histogram of number bytes in transfers, by transfer type",
    ["transfer_type"],
    buckets=PACKAGE_SIZE_BUCKETS,
    registry=REGISTRY,
)

sip_started_counter = Counter(
    "mcpclient_sip_started_total",
    "Number of SIPs started",
    registry=REGISTRY,
)
sip_started_timestamp = Gauge(
    "mcpclient_sip_started_timestamp",
    "Timestamp of most recent SIP started",
    registry=REGISTRY,
)
sip_error_counter = Counter(
    "mcpclient_sip_error_total",
    "Number of SIP failures, by error type",
    ["failure_type"],
    registry=REGISTRY,
)
sip_error_timestamp = Gauge(
    "mcpclient_sip_error_timestamp",
    "Timestamp of most recent SIP failure, by error type",
    ["failure_type"],
    registry=REGISTRY,
)

aips_stored_counter = Counter(
    "mcpclient_aips_stored_total",
    "Number of AIPs stored",
    registry=REGISTRY,
)
dips_stored_counter = Counter(
    "mcpclient_dips_stored_total",
    "Number of DIPs stored",
    registry=REGISTRY,
)
aips_stored_timestamp = Gauge(
    "mcpclient_aips_stored_timestamp",
    "Timestamp of most recent AIP stored",
    registry=REGISTRY,
)
dips_stored_timestamp = Gauge(
    "mcpclient_dips_stored_timestamp",
    "Timestamp of most recent DIP stored",
    registry=REGISTRY,
)
aip_processing_time_histogram = Histogram(
    "mcpclient_aip_processing_seconds",
    "Histogram of AIP processing time, from first file recorded in DB to storage in SS",
    buckets=PROCESSING_TIME_BUCKETS,
    registry=REGISTRY,
)
dip_processing_time_histogram = Histogram(
    "mcpclient_dip_processing_seconds",
    "Histogram of DIP processing time, from first file recorded in DB to storage in SS",
    buckets=PROCESSING_TIME_BUCKETS,
    registry=REGISTRY,
)
aip_files_stored_histogram = Histogram(
    "mcpclient_aip_files_stored",
    "Histogram of number of files stored in AIPs. Note, this includes metadata, derivatives, etc.",
    buckets=PACKAGE_FILE_COUNT_BUCKETS,
    registry=REGISTRY,
)
dip_files_stored_histogram = Histogram(
    "mcpclient_dip_files_stored",
    "Histogram of number of files stored in DIPs.",
    buckets=PACKAGE_FILE_COUNT_BUCKETS,
    registry=REGISTRY,
)
aip_size_histogram = Histogram(
    "mcpclient_aip_size_bytes",
    "Histogram of number of bytes stored in AIPs. Note, this includes metadata, derivatives, etc.",
    buckets=PACKAGE_SIZE_BUCKETS,
    registry=REGISTRY,
)
dip_size_histogram = Histogram(
    "mcpclient_dip_size_bytes",
    "Histogram of number of bytes stored in DIPs. Note, this includes metadata, derivatives, etc.",
    buckets=PACKAGE_SIZE_BUCKETS,
    registry=REGISTRY,
)

# As we track over 1000 formats, the cardinality here is around 3000 and
# well over the recommended number of label values for Prometheus (not over
# 100). This will break down if we start tracking many nodes.
aip_files_stored_by_file_group_and_format_counter = Counter(
    "mcpclient_aip_files_stored_by_file_group_and_format_total",
    "Number of original files stored in AIPs labeled by file group, format name.",
    ["file_group", "format_name"],
    registry=REGISTRY,
)
aip_original_file_timestamps_histogram = Histogram(
    "mcpclient_aip_original_file_timestamps",
    "Histogram of modification times for files stored in AIPs, bucketed by year",
    buckets=[1970, 1980, 1990, 2005, 2010]
    + list(range(2015, datetime.date.today().year + 2))
    + [float("inf")],
    registry=REGISTRY,
)
ss_api_time_counter = Counter(
    "common_ss_api_request_duration_seconds",
    (
        "Total time waiting on the Storage Service API in seconds, labeled by "
        "function name"
    ),
    ["function"],
    registry=REGISTRY,
)
metric_events_applied_counter = Counter(
    "mcpclient_metric_events_applied_total",
    "Number of worker metric events applied in the MCPClient parent process.",
    ["collector", "action"],
    registry=REGISTRY,
)
metric_event_apply_errors_counter = Counter(
    "mcpclient_metric_event_apply_errors_total",
    "Number of worker metric events the MCPClient parent process failed to apply.",
    ["collector", "action"],
    registry=REGISTRY,
)


# There's no central place to pull these constants from currently
FILE_GROUPS = ("original", "derivative", "metadata")
PACKAGE_FAILURE_TYPES = ("fail", "reject")
TRANSFER_TYPES = ("Standard", "Dataverse", "Dspace", "TRIM", "Maildir", "Unknown")

# Map stable event names to parent-owned collectors. Worker code must use these
# keys so event payloads remain small and independent of collector instances.
_COLLECTORS = {
    "job_counter": job_counter,
    "job_processed_timestamp": job_processed_timestamp,
    "job_error_counter": job_error_counter,
    "job_error_timestamp": job_error_timestamp,
    "task_execution_time_histogram": task_execution_time_histogram,
    "database_transaction_duration_histogram": (
        database_transaction_duration_histogram
    ),
    "transfer_started_counter": transfer_started_counter,
    "transfer_started_timestamp": transfer_started_timestamp,
    "transfer_completed_counter": transfer_completed_counter,
    "transfer_completed_timestamp": transfer_completed_timestamp,
    "transfer_error_counter": transfer_error_counter,
    "transfer_error_timestamp": transfer_error_timestamp,
    "transfer_files_histogram": transfer_files_histogram,
    "transfer_size_histogram": transfer_size_histogram,
    "sip_started_counter": sip_started_counter,
    "sip_started_timestamp": sip_started_timestamp,
    "sip_error_counter": sip_error_counter,
    "sip_error_timestamp": sip_error_timestamp,
    "aips_stored_counter": aips_stored_counter,
    "dips_stored_counter": dips_stored_counter,
    "aips_stored_timestamp": aips_stored_timestamp,
    "dips_stored_timestamp": dips_stored_timestamp,
    "aip_processing_time_histogram": aip_processing_time_histogram,
    "dip_processing_time_histogram": dip_processing_time_histogram,
    "aip_files_stored_histogram": aip_files_stored_histogram,
    "dip_files_stored_histogram": dip_files_stored_histogram,
    "aip_size_histogram": aip_size_histogram,
    "dip_size_histogram": dip_size_histogram,
    "aip_files_stored_by_file_group_and_format_counter": (
        aip_files_stored_by_file_group_and_format_counter
    ),
    "aip_original_file_timestamps_histogram": (aip_original_file_timestamps_histogram),
    "ss_api_time_counter": ss_api_time_counter,
}


T = TypeVar("T")


def skip_if_prometheus_disabled(
    func: Callable[..., Optional[T]],
) -> Callable[..., Optional[T]]:
    @functools.wraps(func)
    def wrapper(*args: object, **kwds: object) -> Optional[T]:
        if settings.PROMETHEUS_ENABLED:
            return func(*args, **kwds)
        return None

    return wrapper


def configure_event_queue(event_queue: Optional[MetricQueue]) -> None:
    """Route metric updates through a queue.

    MCPClient workers call this with the parent-owned queue before processing
    Gearman jobs. The parent keeps the default ``None`` value and applies
    metrics directly.
    """
    global _EVENT_QUEUE
    with _EVENT_QUEUE_LOCK:
        _EVENT_QUEUE = event_queue


@contextmanager
def client_script_context(script_name: str) -> Iterator[None]:
    token = _CURRENT_SCRIPT_NAME.set(script_name)
    try:
        yield
    finally:
        _CURRENT_SCRIPT_NAME.reset(token)


def apply_event(event: MetricEvent) -> None:
    """Apply one worker metric event to the parent registry."""
    collector = _COLLECTORS[event.collector]
    metric = collector.labels(**dict(event.labels)) if event.labels else collector

    if event.action == "inc":
        cast(Counter, metric).inc(event.value)
    elif event.action == "set":
        cast(Gauge, metric).set(event.value)
    elif event.action == "set_max":
        key = (event.collector, event.labels)
        with _GAUGE_MAX_VALUES_LOCK:
            current = _GAUGE_MAX_VALUES.get(key)
            if current is None or event.value > current:
                _GAUGE_MAX_VALUES[key] = event.value
                cast(Gauge, metric).set(event.value)
    elif event.action == "observe":
        cast(Histogram, metric).observe(event.value)
    else:
        raise ValueError(f"Unknown metric event action: {event.action}")

    metric_events_applied_counter.labels(
        collector=event.collector,
        action=event.action,
    ).inc()


class EventListener:
    """Drain worker metric events and apply them in the parent process."""

    def __init__(self, event_queue: MetricQueue) -> None:
        self.event_queue = event_queue
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._listen,
            name="mcpclient-metrics-listener",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
        self._drain()

    def _listen(self) -> None:
        while not self._stop.is_set():
            try:
                event = self.event_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            self._apply(event)

    def _drain(self) -> None:
        while True:
            try:
                event = self.event_queue.get_nowait()
            except queue.Empty:
                return
            self._apply(event)

    @staticmethod
    def _apply(event: Any) -> None:
        if isinstance(event, MetricEvent):
            try:
                apply_event(event)
            except Exception:
                metric_event_apply_errors_counter.labels(
                    collector=event.collector,
                    action=event.action,
                ).inc()
                logger.exception("Failed to apply MCPClient metric event: %r", event)


def _log_queue_write_failure_once(event: MetricEvent) -> None:
    """Log the first metric queue write failure in this process.

    Metrics are intentionally best-effort. A single warning makes event loss
    visible without turning a full or closed queue into repeated worker log
    noise.
    """
    global _QUEUE_WRITE_FAILURE_LOGGED
    with _QUEUE_WRITE_FAILURE_LOCK:
        if _QUEUE_WRITE_FAILURE_LOGGED:
            return
        _QUEUE_WRITE_FAILURE_LOGGED = True

    logger.warning(
        "Dropping MCPClient metric event after queue write failure: %r", event
    )


def _record_event(
    collector: str,
    action: str,
    labels: Optional[dict[str, str]] = None,
    value: float = 1.0,
) -> None:
    event = MetricEvent(
        collector=collector,
        action=action,
        labels=tuple(sorted((labels or {}).items())),
        value=value,
    )
    with _EVENT_QUEUE_LOCK:
        event_queue = _EVENT_QUEUE

    if event_queue is None:
        apply_event(event)
        return

    try:
        event_queue.put_nowait(event)
    except Exception:
        _log_queue_write_failure_once(event)
        # Metrics must not affect task execution.
        pass


def _inc(
    collector: str,
    labels: Optional[dict[str, str]] = None,
    amount: float = 1.0,
) -> None:
    _record_event(collector, "inc", labels, amount)


def _set(
    collector: str,
    labels: Optional[dict[str, str]] = None,
    value: float = 0.0,
) -> None:
    _record_event(collector, "set", labels, value)


def _set_max(
    collector: str,
    labels: Optional[dict[str, str]] = None,
    value: float = 0.0,
) -> None:
    _record_event(collector, "set_max", labels, value)


def _set_to_current_time(
    collector: str,
    labels: Optional[dict[str, str]] = None,
) -> None:
    _set_max(collector, labels, time.time())


def _observe(
    collector: str,
    labels: Optional[dict[str, str]] = None,
    value: float = 0.0,
) -> None:
    _record_event(collector, "observe", labels, value)


class _StorageServiceAPITimeCounterChild:
    """Counter child compatible with common_metrics.ss_api_time_counter."""

    def __init__(self, labels: dict[str, str]) -> None:
        self.labels = labels

    def inc(self, amount: float = 1.0) -> None:
        _inc("ss_api_time_counter", self.labels, amount)


class _StorageServiceAPITimeCounter:
    """Bridge common Storage Service API timing into MCPClient metrics.

    The shared ``storageService`` helpers call ``common_metrics.ss_api_timer``,
    which increments ``common_metrics.ss_api_time_counter``. Replacing that
    counter in MCPClient keeps ``common_ss_api_request_duration_seconds`` in
    MCPClient scrapes through the parent-owned registry.
    """

    def labels(
        self, *labelvalues: str, **labelkwargs: str
    ) -> _StorageServiceAPITimeCounterChild:
        labels = dict(labelkwargs)
        if labelvalues:
            labels["function"] = labelvalues[0]

        return _StorageServiceAPITimeCounterChild(labels)


cast(Any, common_metrics).ss_api_time_counter = _StorageServiceAPITimeCounter()


@contextmanager
def time_task_execution(script_name: str) -> Iterator[None]:
    start = time.monotonic()
    try:
        yield
    finally:
        _observe(
            "task_execution_time_histogram",
            {"script_name": script_name},
            time.monotonic() - start,
        )


def init_counter_labels() -> None:
    # Zero our counters to start, by intializing all labels. Non-zero starting points
    # cause problems when measuring rates.
    modules_config = configparser.RawConfigParser()
    modules_config.read(settings.CLIENT_MODULES_FILE)
    for script_name, _ in modules_config.items("supportedBatchCommands"):
        task_execution_time_histogram.labels(script_name=script_name)
        database_transaction_duration_histogram.labels(script_name=script_name)
        job_counter.labels(script_name=script_name)
        job_processed_timestamp.labels(script_name=script_name)
        job_error_counter.labels(script_name=script_name)
        job_error_timestamp.labels(script_name=script_name)

    for transfer_type in TRANSFER_TYPES:
        transfer_started_counter.labels(transfer_type=transfer_type)
        transfer_started_timestamp.labels(transfer_type=transfer_type)
        transfer_completed_counter.labels(transfer_type=transfer_type)
        transfer_completed_timestamp.labels(transfer_type=transfer_type)
        transfer_files_histogram.labels(transfer_type=transfer_type)
        transfer_size_histogram.labels(transfer_type=transfer_type)

        for failure_type in PACKAGE_FAILURE_TYPES:
            transfer_error_counter.labels(
                transfer_type=transfer_type, failure_type=failure_type
            )
            transfer_error_timestamp.labels(
                transfer_type=transfer_type, failure_type=failure_type
            )

    for failure_type in PACKAGE_FAILURE_TYPES:
        sip_error_counter.labels(failure_type=failure_type)
        sip_error_timestamp.labels(failure_type=failure_type)

    if settings.PROMETHEUS_DETAILED_METRICS:
        for format_name in FormatVersion.objects.values_list("description", flat=True):
            for file_group in FILE_GROUPS:
                aip_files_stored_by_file_group_and_format_counter.labels(
                    file_group=file_group, format_name=format_name
                )


@skip_if_prometheus_disabled
def start_prometheus_server() -> tuple[WSGIServer, threading.Thread]:
    init_counter_labels()

    result: tuple[WSGIServer, threading.Thread] = start_http_server(
        settings.PROMETHEUS_BIND_PORT,
        addr=settings.PROMETHEUS_BIND_ADDRESS,
        registry=REGISTRY,
    )
    return result


@skip_if_prometheus_disabled
def job_completed(script_name: str) -> None:
    labels = {"script_name": script_name}
    _inc("job_counter", labels)
    _set_to_current_time("job_processed_timestamp", labels)


@skip_if_prometheus_disabled
def job_failed(script_name: str) -> None:
    labels = {"script_name": script_name}
    _inc("job_counter", labels)
    _inc("job_error_counter", labels)
    _set_to_current_time("job_error_timestamp", labels)


@skip_if_prometheus_disabled
def database_transaction_observed(duration: float) -> None:
    script_name = _CURRENT_SCRIPT_NAME.get()
    if script_name is None:
        return
    _observe(
        "database_transaction_duration_histogram",
        {"script_name": script_name},
        duration,
    )


def _get_file_group(raw_file_group_use: str) -> str:
    """Convert one of the file group use values we know about into
    the smaller subset that we track:

    original -> original
    metadata -> metadata
    submissionDocumentation -> metadata
    access -> derivative
    thumbnail -> derivative
    preservation -> derivative
    aip -> derivative
    """
    raw_file_group_use = raw_file_group_use.lower()
    if raw_file_group_use == "original":
        return "original"
    elif raw_file_group_use in ("metadata", "submissiondocumentation"):
        return "metadata"
    else:
        return "derivative"


@skip_if_prometheus_disabled
def aip_stored(sip_uuid: str, size: int) -> None:
    _inc("aips_stored_counter")
    _set_to_current_time("aips_stored_timestamp")
    _observe("aip_size_histogram", value=size)

    try:
        earliest_file = File.objects.filter(sip_id=sip_uuid).earliest("enteredsystem")
    except File.DoesNotExist:
        pass
    else:
        duration = (timezone.now() - earliest_file.enteredsystem).total_seconds()
        _observe("aip_processing_time_histogram", value=duration)

    # We do two queries here, as we may not have format information for everything
    total_file_count = File.objects.filter(sip_id=sip_uuid).count()
    _observe("aip_files_stored_histogram", value=total_file_count)

    if settings.PROMETHEUS_DETAILED_METRICS:
        # TODO: This could probably benefit from batching with prefetches. Using just
        # prefetches will likely break down with very large numbers of files.
        for file_obj in (
            File.objects.filter(sip_id=sip_uuid).exclude(filegrpuse="aip").iterator()
        ):
            if file_obj.filegrpuse.lower() == "original" and file_obj.modificationtime:
                _observe(
                    "aip_original_file_timestamps_histogram",
                    value=file_obj.modificationtime.year,
                )

            file_group = _get_file_group(file_obj.filegrpuse)
            format_name = "Unknown"

            format_version_m2m = (
                FileFormatVersion.objects.select_related(
                    "format_version", "format_version__format"
                )
                .filter(file_uuid=file_obj.uuid)
                .first()
            )
            if (
                format_version_m2m
                and format_version_m2m.format_version
                and format_version_m2m.format_version.format
            ):
                format_name = format_version_m2m.format_version.format.description

            _inc(
                "aip_files_stored_by_file_group_and_format_counter",
                {"file_group": file_group, "format_name": format_name},
            )


@skip_if_prometheus_disabled
def dip_stored(sip_uuid: str, size: int) -> None:
    _inc("dips_stored_counter")
    _set_to_current_time("dips_stored_timestamp")
    _observe("dip_size_histogram", value=size)

    try:
        earliest_file = File.objects.filter(sip_id=sip_uuid).earliest("enteredsystem")
    except File.DoesNotExist:
        pass
    else:
        duration = (timezone.now() - earliest_file.enteredsystem).total_seconds()
        _observe("dip_processing_time_histogram", value=duration)

    file_count = File.objects.filter(sip_id=sip_uuid).count()
    _observe("dip_files_stored_histogram", value=file_count)


@skip_if_prometheus_disabled
def transfer_started(transfer_type: str) -> None:
    if not transfer_type:
        transfer_type = "Unknown"
    labels = {"transfer_type": transfer_type}
    _inc("transfer_started_counter", labels)
    _set_to_current_time("transfer_started_timestamp", labels)


@skip_if_prometheus_disabled
def transfer_completed(transfer_uuid: str) -> None:
    try:
        transfer = Transfer.objects.get(uuid=transfer_uuid)
    except Transfer.DoesNotExist:
        return

    transfer_type = transfer.type or "Unknown"

    labels = {"transfer_type": transfer_type}
    _inc("transfer_completed_counter", labels)
    _set_to_current_time("transfer_completed_timestamp", labels)

    file_queryset = File.objects.filter(transfer=transfer)
    file_count = file_queryset.count()
    _observe("transfer_files_histogram", labels, file_count)

    transfer_size = file_queryset.aggregate(total_size=Sum("size"))
    _observe("transfer_size_histogram", labels, transfer_size["total_size"] or 0)


@skip_if_prometheus_disabled
def transfer_failed(transfer_type: str, failure_type: str) -> None:
    if not transfer_type:
        transfer_type = "Unknown"

    labels = {"transfer_type": transfer_type, "failure_type": failure_type}
    _inc("transfer_error_counter", labels)
    _set_to_current_time("transfer_error_timestamp", labels)


@skip_if_prometheus_disabled
def sip_started() -> None:
    _inc("sip_started_counter")
    _set_to_current_time("sip_started_timestamp")


@skip_if_prometheus_disabled
def sip_failed(failure_type: str) -> None:
    labels = {"failure_type": failure_type}
    _inc("sip_error_counter", labels)
    _set_to_current_time("sip_error_timestamp", labels)
