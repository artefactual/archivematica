"""
Exposes various metrics via Prometheus.
"""
from __future__ import absolute_import, unicode_literals

import functools

from django.conf import settings
from prometheus_client import Counter, Gauge, Summary, start_http_server


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
aips_stored_counter = Counter("mcpclient_aips_stored_total", "Number of AIPs stored")
dips_stored_counter = Counter("mcpclient_dips_stored_total", "Number of DIPs stored")
aips_stored_timestamp = Gauge(
    "mcpclient_aips_stored_timestamp", "Timestamp of most recent AIP stored"
)
dips_stored_timestamp = Gauge(
    "mcpclient_dips_stored_timestamp", "Timestamp of most recent DIP stored"
)


def skip_if_prometheus_disabled(func):
    @functools.wraps(func)
    def wrapper(*args, **kwds):
        if settings.PROMETHEUS_ENABLED:
            return func(*args, **kwds)
        return None

    return wrapper


@skip_if_prometheus_disabled
def start_prometheus_server():
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
def aip_stored():
    aips_stored_counter.inc()
    aips_stored_timestamp.set_to_current_time()


@skip_if_prometheus_disabled
def dip_stored():
    dips_stored_counter.inc()
    dips_stored_timestamp.set_to_current_time()
