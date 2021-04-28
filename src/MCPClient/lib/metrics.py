"""
Exposes various metrics via Prometheus.
"""
from __future__ import absolute_import, unicode_literals

import six.moves.configparser
import datetime
import functools
import os

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server

from fpr.models import FormatVersion
from main.models import File, FileFormatVersion, Transfer

from common_metrics import (
    PACKAGE_FILE_COUNT_BUCKETS,
    PACKAGE_SIZE_BUCKETS,
    PROCESSING_TIME_BUCKETS,
    TASK_DURATION_BUCKETS,
)
from version import get_full_version
from six.moves import range


job_counter = Counter(
    "mcpclient_job_total",
    "Number of jobs processed, labeled by script",
    ["script_name"],
)
job_processed_timestamp = Gauge(
    "mcpclient_job_success_timestamp",
    "Timestamp of most recent job processed, labeled by script",
    ["script_name"],
)
job_error_counter = Counter(
    "mcpclient_job_error_total",
    "Number of failures processing jobs, labeled by script",
    ["script_name"],
)
job_error_timestamp = Gauge(
    "mcpclient_job_error_timestamp",
    "Timestamp of most recent job failure, labeled by script",
    ["script_name"],
)

task_execution_time_histogram = Histogram(
    "mcpclient_task_execution_time_seconds",
    "Histogram of worker task execution times in seconds, labeled by script",
    ["script_name"],
    buckets=TASK_DURATION_BUCKETS,
)
waiting_for_gearman_time_counter = Counter(
    "mcpclient_gearman_sleep_time_seconds",
    "Total worker sleep after gearman error times in seconds",
)

transfer_started_counter = Counter(
    "mcpclient_transfer_started_total",
    "Number of Transfers started, by transfer type",
    ["transfer_type"],
)
transfer_started_timestamp = Gauge(
    "mcpclient_transfer_started_timestamp",
    "Timestamp of most recent transfer started, by transfer type",
    ["transfer_type"],
)
transfer_completed_counter = Counter(
    "mcpclient_transfer_completed_total",
    "Number of Transfers completed, by transfer type",
    ["transfer_type"],
)
transfer_completed_timestamp = Gauge(
    "mcpclient_transfer_completed_timestamp",
    "Timestamp of most recent transfer completed, by transfer type",
    ["transfer_type"],
)
transfer_error_counter = Counter(
    "mcpclient_transfer_error_total",
    "Number of transfer failures, by transfer type, error type",
    ["transfer_type", "failure_type"],
)
transfer_error_timestamp = Gauge(
    "mcpclient_transfer_error_timestamp",
    "Timestamp of most recent transfer failure, by transfer type, error type",
    ["transfer_type", "failure_type"],
)
transfer_files_histogram = Histogram(
    "mcpclient_transfer_files",
    "Histogram of number of files included in transfers, by transfer type",
    ["transfer_type"],
    buckets=PACKAGE_FILE_COUNT_BUCKETS,
)
transfer_size_histogram = Histogram(
    "mcpclient_transfer_size_bytes",
    "Histogram of number bytes in transfers, by transfer type",
    ["transfer_type"],
    buckets=PACKAGE_SIZE_BUCKETS,
)

sip_started_counter = Counter("mcpclient_sip_started_total", "Number of SIPs started")
sip_started_timestamp = Gauge(
    "mcpclient_sip_started_timestamp", "Timestamp of most recent SIP started"
)
sip_error_counter = Counter(
    "mcpclient_sip_error_total",
    "Number of SIP failures, by error type",
    ["failure_type"],
)
sip_error_timestamp = Gauge(
    "mcpclient_sip_error_timestamp",
    "Timestamp of most recent SIP failure, by error type",
    ["failure_type"],
)

aips_stored_counter = Counter("mcpclient_aips_stored_total", "Number of AIPs stored")
dips_stored_counter = Counter("mcpclient_dips_stored_total", "Number of DIPs stored")
aips_stored_timestamp = Gauge(
    "mcpclient_aips_stored_timestamp", "Timestamp of most recent AIP stored"
)
dips_stored_timestamp = Gauge(
    "mcpclient_dips_stored_timestamp", "Timestamp of most recent DIP stored"
)
aip_processing_time_histogram = Histogram(
    "mcpclient_aip_processing_seconds",
    "Histogram of AIP processing time, from first file recorded in DB to storage in SS",
    buckets=PROCESSING_TIME_BUCKETS,
)
dip_processing_time_histogram = Histogram(
    "mcpclient_dip_processing_seconds",
    "Histogram of DIP processing time, from first file recorded in DB to storage in SS",
    buckets=PROCESSING_TIME_BUCKETS,
)
aip_files_stored_histogram = Histogram(
    "mcpclient_aip_files_stored",
    "Histogram of number of files stored in AIPs. Note, this includes metadata, derivatives, etc.",
    buckets=PACKAGE_FILE_COUNT_BUCKETS,
)
dip_files_stored_histogram = Histogram(
    "mcpclient_dip_files_stored",
    "Histogram of number of files stored in DIPs.",
    buckets=PACKAGE_FILE_COUNT_BUCKETS,
)
aip_size_histogram = Histogram(
    "mcpclient_aip_size_bytes",
    "Histogram of number of bytes stored in AIPs. Note, this includes metadata, derivatives, etc.",
    buckets=PACKAGE_SIZE_BUCKETS,
)
dip_size_histogram = Histogram(
    "mcpclient_dip_size_bytes",
    "Histogram of number of bytes stored in DIPs. Note, this includes metadata, derivatives, etc.",
    buckets=PACKAGE_SIZE_BUCKETS,
)

# As we track over 1000 formats, the cardinality here is around 3000 and
# well over the recommended number of label values for Prometheus (not over
# 100). This will break down if we start tracking many nodes.
aip_files_stored_by_file_group_and_format_counter = Counter(
    "mcpclient_aip_files_stored_by_file_group_and_format_total",
    "Number of original files stored in AIPs labeled by file group, format name.",
    ["file_group", "format_name"],
)
aip_original_file_timestamps_histogram = Histogram(
    "mcpclient_aip_original_file_timestamps",
    "Histogram of modification times for files stored in AIPs, bucketed by year",
    buckets=[1970, 1980, 1990, 2005, 2010]
    + list(range(2015, datetime.date.today().year + 2))
    + [float("inf")],
)

archivematica_info = Info("archivematica_version", "Archivematica version info")
environment_info = Info("environment_variables", "Environment Variables")


# There's no central place to pull these constants from currently
FILE_GROUPS = ("original", "derivative", "metadata")
PACKAGE_FAILURE_TYPES = ("fail", "reject")
TRANSFER_TYPES = ("Standard", "Dataverse", "Dspace", "TRIM", "Maildir", "Unknown")


def skip_if_prometheus_disabled(func):
    @functools.wraps(func)
    def wrapper(*args, **kwds):
        if settings.PROMETHEUS_ENABLED:
            return func(*args, **kwds)
        return None

    return wrapper


def init_counter_labels():
    # Zero our counters to start, by intializing all labels. Non-zero starting points
    # cause problems when measuring rates.
    modules_config = six.moves.configparser.RawConfigParser()
    modules_config.read(settings.CLIENT_MODULES_FILE)
    for script_name, _ in modules_config.items("supportedBatchCommands"):
        job_counter.labels(script_name=script_name)
        job_processed_timestamp.labels(script_name=script_name)
        job_error_counter.labels(script_name=script_name)
        job_error_timestamp.labels(script_name=script_name)
        task_execution_time_histogram.labels(script_name=script_name)

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

    for format_name in FormatVersion.objects.values_list("description", flat=True):
        for file_group in FILE_GROUPS:
            aip_files_stored_by_file_group_and_format_counter.labels(
                file_group=file_group, format_name=format_name
            )


@skip_if_prometheus_disabled
def start_prometheus_server():
    init_counter_labels()

    archivematica_info.info({"version": get_full_version()})
    environment_info.info(os.environ)

    return start_http_server(
        settings.PROMETHEUS_BIND_PORT, addr=settings.PROMETHEUS_BIND_ADDRESS
    )


@skip_if_prometheus_disabled
def job_completed(script_name):
    job_counter.labels(script_name=script_name).inc()
    job_processed_timestamp.labels(script_name=script_name).set_to_current_time()


@skip_if_prometheus_disabled
def job_failed(script_name):
    job_counter.labels(script_name=script_name).inc()
    job_error_counter.labels(script_name=script_name).inc()
    job_error_timestamp.labels(script_name=script_name).set_to_current_time()


def _get_file_group(raw_file_group_use):
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
def aip_stored(sip_uuid, size):
    aips_stored_counter.inc()
    aips_stored_timestamp.set_to_current_time()
    aip_size_histogram.observe(size)

    try:
        earliest_file = File.objects.filter(sip_id=sip_uuid).earliest("enteredsystem")
    except File.DoesNotExist:
        pass
    else:
        duration = (timezone.now() - earliest_file.enteredsystem).total_seconds()
        aip_processing_time_histogram.observe(duration)

    # We do two queries here, as we may not have format information for everything
    total_file_count = File.objects.filter(sip_id=sip_uuid).count()
    aip_files_stored_histogram.observe(total_file_count)

    # TODO: This could probably benefit from batching with prefetches. Using just
    # prefetches will likely break down with very large numbers of files.
    for file_obj in (
        File.objects.filter(sip_id=sip_uuid).exclude(filegrpuse="aip").iterator()
    ):
        if file_obj.filegrpuse.lower() == "original" and file_obj.modificationtime:
            aip_original_file_timestamps_histogram.observe(
                file_obj.modificationtime.year
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

        aip_files_stored_by_file_group_and_format_counter.labels(
            file_group=file_group, format_name=format_name
        ).inc()


@skip_if_prometheus_disabled
def dip_stored(sip_uuid, size):
    dips_stored_counter.inc()
    dips_stored_timestamp.set_to_current_time()
    dip_size_histogram.observe(size)

    try:
        earliest_file = File.objects.filter(sip_id=sip_uuid).earliest("enteredsystem")
    except File.DoesNotExist:
        pass
    else:
        duration = (timezone.now() - earliest_file.enteredsystem).total_seconds()
        dip_processing_time_histogram.observe(duration)

    file_count = File.objects.filter(sip_id=sip_uuid).count()
    dip_files_stored_histogram.observe(file_count)


@skip_if_prometheus_disabled
def transfer_started(transfer_type):
    if not transfer_type:
        transfer_type = "Unknown"
    transfer_started_counter.labels(transfer_type=transfer_type).inc()
    transfer_started_timestamp.labels(transfer_type=transfer_type).set_to_current_time()


@skip_if_prometheus_disabled
def transfer_completed(transfer_uuid):
    try:
        transfer = Transfer.objects.get(uuid=transfer_uuid)
    except Transfer.DoesNotExist:
        return

    transfer_type = transfer.type or "Unknown"

    transfer_completed_counter.labels(transfer_type=transfer_type).inc()
    transfer_completed_timestamp.labels(
        transfer_type=transfer_type
    ).set_to_current_time()

    file_queryset = File.objects.filter(transfer=transfer)
    file_count = file_queryset.count()
    transfer_files_histogram.labels(transfer_type=transfer_type).observe(file_count)

    transfer_size = file_queryset.aggregate(total_size=Sum("size"))
    transfer_size_histogram.labels(transfer_type=transfer_type).observe(
        transfer_size["total_size"]
    )


@skip_if_prometheus_disabled
def transfer_failed(transfer_type, failure_type):
    if not transfer_type:
        transfer_type = "Unknown"

    transfer_error_counter.labels(
        transfer_type=transfer_type, failure_type=failure_type
    ).inc()
    transfer_error_timestamp.labels(
        transfer_type=transfer_type, failure_type=failure_type
    ).set_to_current_time()


@skip_if_prometheus_disabled
def sip_started():
    sip_started_counter.inc()
    sip_started_timestamp.set_to_current_time()


@skip_if_prometheus_disabled
def sip_failed(failure_type):
    sip_error_counter.labels(failure_type=failure_type).inc()
    sip_error_timestamp.labels(failure_type=failure_type).set_to_current_time()
