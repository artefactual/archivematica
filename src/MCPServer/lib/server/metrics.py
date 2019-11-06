# -*- coding: utf-8 -*-

"""
Exposes various metrics via Prometheus.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import functools
import os

from django.conf import settings
from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server

from common_metrics import TASK_DURATION_BUCKETS
from version import get_full_version


gearman_active_jobs_gauge = Gauge(
    "mcpserver_gearman_active_jobs", "Number of gearman jobs currently being processed"
)
gearman_pending_jobs_gauge = Gauge(
    "mcpserver_gearman_pending_jobs", "Number of gearman jobs pending submission"
)
task_counter = Counter(
    "mcpserver_task_total",
    "Number of tasks processed, labeled by task group, task name",
    ["task_group_name", "task_name"],
)
task_error_counter = Counter(
    "mcpserver_task_error_total",
    "Number of failures processing tasks, labeled by task group, task name",
    ["task_group_name", "task_name"],
)
task_success_timestamp = Gauge(
    "mcpserver_task_success_timestamp",
    "Most recent successfully processed task, labeled by task group, task name",
    ["task_group_name", "task_name"],
)
task_error_timestamp = Gauge(
    "mcpserver_task_error_timestamp",
    "Most recent failure when processing a task, labeled by task group, task name",
    ["task_group_name", "task_name"],
)
task_duration_histogram = Histogram(
    "mcpserver_task_duration_seconds",
    "Histogram of task processing durations in seconds, labeled by script name",
    ["script_name"],
    buckets=TASK_DURATION_BUCKETS,
)

archivematica_info = Info("archivematica_version", "Archivematica version info")
environment_info = Info("environment_variables", "Environment Variables")


active_package_gauge = Gauge(
    "mcpserver_active_packages", "Number of currently active packages"
)
active_jobs_gauge = Gauge("mcpserver_active_jobs", "Number of currently active jobs")
job_queue_length_gauge = Gauge(
    "mcpserver_active_package_job_queue_length",
    "Number of queued jobs related to currently active packages",
)
package_queue_length_gauge = Gauge(
    "mcpserver_package_queue_length", "Number of queued packages", ["package_type"]
)

PACKAGE_TYPES = ("Transfer", "SIP", "DIP")


def skip_if_prometheus_disabled(func):
    @functools.wraps(func)
    def wrapper(*args, **kwds):
        if settings.PROMETHEUS_ENABLED:
            return func(*args, **kwds)
        return None

    return wrapper


@skip_if_prometheus_disabled
def init_labels(workflow):
    """Zero to start, by intializing all labels. Non-zero starting points
    cause problems when measuring rates.
    """
    for package_type in PACKAGE_TYPES:
        package_queue_length_gauge.labels(package_type=package_type)

    for link in workflow.get_links().values():
        group_name = link.get_label("group", "en")
        task_name = link.get_label("description", "en")
        script_name = link.config.get("execute", "").lower()

        task_counter.labels(task_group_name=group_name, task_name=task_name)
        task_error_counter.labels(task_group_name=group_name, task_name=task_name)
        task_success_timestamp.labels(task_group_name=group_name, task_name=task_name)
        task_error_timestamp.labels(task_group_name=group_name, task_name=task_name)
        task_duration_histogram.labels(script_name=script_name)


@skip_if_prometheus_disabled
def start_prometheus_server():
    archivematica_info.info({"version": get_full_version()})
    environment_info.info(os.environ)

    return start_http_server(
        settings.PROMETHEUS_BIND_PORT, addr=settings.PROMETHEUS_BIND_ADDRESS
    )


@skip_if_prometheus_disabled
def task_completed(task, job):
    if task.finished_timestamp is None:
        return

    duration = (task.finished_timestamp - task.start_timestamp).total_seconds()

    task_counter.labels(task_group_name=job.group, task_name=job.description).inc()
    task_success_timestamp.labels(
        task_group_name=job.group, task_name=job.description
    ).set_to_current_time()
    task_duration_histogram.labels(script_name=job.name).observe(duration)


@skip_if_prometheus_disabled
def task_failed(task, job):
    task_error_timestamp.labels(
        task_group_name=job.group, task_name=job.description
    ).set_to_current_time()
    task_error_counter.labels(
        task_group_name=job.group, task_name=job.description
    ).inc()
    task_counter.labels(task_group_name=job.group, task_name=job.description).inc()
