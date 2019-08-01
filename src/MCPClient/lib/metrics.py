"""
Exposes various metrics via Prometheus.
"""
from __future__ import absolute_import, unicode_literals

import ConfigParser
import functools

from django.conf import settings
from django.utils import timezone
from prometheus_client import Counter, Gauge, Summary, start_http_server

from main.models import File


job_counter = Counter(
    "mcpclient_job_total", "Number of jobs processed", ["script_name"]
)
job_processed_timestamp = Gauge(
    "mcpclient_job_success_timestamp",
    "Timestamp of most recent job processed",
    ["script_name"],
)
job_error_counter = Counter(
    "mcpclient_job_error_total", "Number of failures processing jobs", ["script_name"]
)
job_error_timestamp = Gauge(
    "mcpclient_job_error_timestamp",
    "Timestamp of most recent job failure",
    ["script_name"],
)

task_execution_time_summary = Summary(
    "mcpclient_task_execution_time_seconds",
    "Summary of worker task execution times in seconds",
    ["script_name"],
)
waiting_for_gearman_time_summary = Summary(
    "mcpclient_gearman_sleep_time_seconds",
    "Summary of worker sleep after gearman error times in seconds",
)

transfer_started_counter = Counter(
    "mcpclient_transfer_started_total", "Number of Transfers started", ["transfer_type"]
)
transfer_started_timestamp = Gauge(
    "mcpclient_transfer_started_timestamp",
    "Timestamp of most recent transfer started",
    ["transfer_type"],
)
transfer_error_counter = Counter(
    "mcpclient_transfer_error_total",
    "Number of transfer failures",
    ["transfer_type", "failure_type"],
)
transfer_error_timestamp = Gauge(
    "mcpclient_transfer_error_timestamp",
    "Timestamp of most recent transfer failure",
    ["transfer_type", "failure_type"],
)

sip_started_counter = Counter("mcpclient_sip_started_total", "Number of SIPs started")
sip_started_timestamp = Gauge(
    "mcpclient_sip_started_timestamp", "Timestamp of most recent SIP started"
)
sip_error_counter = Counter(
    "mcpclient_sip_error_total", "Number of SIP failures", ["failure_type"]
)
sip_error_timestamp = Gauge(
    "mcpclient_sip_error_timestamp",
    "Timestamp of most recent SIP failure",
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
aip_processing_time_summary = Summary(
    "mcpclient_aip_processing_seconds",
    "AIP processing time, from first file recorded in DB to storage in SS",
)
dip_processing_time_summary = Summary(
    "mcpclient_dip_processing_seconds",
    "DIP processing time, from first file recorded in DB to storage in SS",
)
aip_files_stored_counter = Counter(
    "mcpclient_aip_files_stored_total", "Number of files stored in AIPs"
)
dip_files_stored_counter = Counter(
    "mcpclient_dip_files_stored_total", "Number of files stored in DIPs"
)
aip_size_counter = Counter("mcpclient_aip_size_bytes", "Number of bytes stored in AIPs")
dip_size_counter = Counter("mcpclient_dip_size_bytes", "Number of bytes stored in DIPs")


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
    modules_config = ConfigParser.RawConfigParser()
    modules_config.read(settings.CLIENT_MODULES_FILE)
    for script_name, _ in modules_config.items("supportedBatchCommands"):
        job_counter.labels(script_name=script_name)
        job_processed_timestamp.labels(script_name=script_name)
        job_error_counter.labels(script_name=script_name)
        job_error_timestamp.labels(script_name=script_name)
        task_execution_time_summary.labels(script_name=script_name)

    failure_types = ("fail", "reject")

    for transfer_type in ("Standard", "Dataverse", "Dspace", "TRIM", "Maildir"):
        transfer_started_counter.labels(transfer_type=transfer_type)
        transfer_started_timestamp.labels(transfer_type=transfer_type)

        for failure_type in failure_types:
            transfer_error_counter.labels(
                transfer_type=transfer_type, failure_type=failure_type
            )
            transfer_error_timestamp.labels(
                transfer_type=transfer_type, failure_type=failure_type
            )

    for failure_type in failure_types:
        sip_error_counter.labels(failure_type=failure_type)
        sip_error_timestamp.labels(failure_type=failure_type)


@skip_if_prometheus_disabled
def start_prometheus_server():
    init_counter_labels()

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


@skip_if_prometheus_disabled
def aip_stored(sip_uuid, size):
    aips_stored_counter.inc()
    aips_stored_timestamp.set_to_current_time()
    aip_size_counter.inc(size)

    try:
        earliest_file = File.objects.filter(sip_id=sip_uuid).earliest("enteredsystem")
    except File.DoesNotExist:
        pass
    else:
        duration = (timezone.now() - earliest_file.enteredsystem).total_seconds()
        aip_processing_time_summary.observe(duration)

    file_count = File.objects.filter(sip_id=sip_uuid).count()
    aip_files_stored_counter.inc(file_count)


@skip_if_prometheus_disabled
def dip_stored(sip_uuid, size):
    dips_stored_counter.inc()
    dips_stored_timestamp.set_to_current_time()
    dip_size_counter.inc(size)

    try:
        earliest_file = File.objects.filter(sip_id=sip_uuid).earliest("enteredsystem")
    except File.DoesNotExist:
        pass
    else:
        duration = (timezone.now() - earliest_file.enteredsystem).total_seconds()
        dip_processing_time_summary.observe(duration)

    file_count = File.objects.filter(sip_id=sip_uuid).count()
    dip_files_stored_counter.inc(file_count)


@skip_if_prometheus_disabled
def transfer_started(transfer_type):
    transfer_started_counter.labels(transfer_type=transfer_type).inc()
    transfer_started_timestamp.labels(transfer_type=transfer_type).set_to_current_time()


@skip_if_prometheus_disabled
def transfer_failed(transfer_type, failure_type):
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
