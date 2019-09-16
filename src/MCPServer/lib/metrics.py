"""
Exposes various metrics via Prometheus.
"""
from __future__ import absolute_import, unicode_literals

import functools

from django.conf import settings
from prometheus_client import Counter, Gauge, Summary, start_http_server


active_task_group_gauge = Gauge(
    "mcpserver_active_task_groups", "Number of task groups currently being processed"
)
gearman_active_jobs_gauge = Gauge(
    "mcpserver_gearman_active_jobs", "Number of gearman jobs currently being processed"
)
gearman_pending_jobs_gauge = Gauge(
    "mcpserver_gearman_pending_jobs", "Number of gearman jobs pending submission"
)
task_counter = Counter(
    "mcpserver_task_total",
    "Number of tasks processed",
    ["task_group_name", "task_name"],
)
task_error_counter = Counter(
    "mcpserver_task_error_total",
    "Number of failures processing tasks",
    ["task_group_name", "task_name"],
)
task_success_timestamp = Gauge(
    "mcpserver_task_success_timestamp",
    "Most recent successfully processed task",
    ["task_group_name", "task_name"],
)
task_error_timestamp = Gauge(
    "mcpserver_task_error_timestamp",
    "Most recent failure when processing a task",
    ["task_group_name", "task_name"],
)
task_duration_summary = Summary(
    "mcpserver_task_duration_seconds",
    "Summary of task durations in seconds",
    ["task_group_name", "task_name"],
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
def update_job_status(active_task_groups_by_uuid, running_gearman_jobs, pending_jobs):
    group_uuids = [
        task_group.task_group.unit_uuid()
        for task_group in active_task_groups_by_uuid.values()
    ]
    active_task_group_gauge.set(len(set(group_uuids)))

    gearman_pending_jobs_gauge.set(len(pending_jobs))
    gearman_active_jobs_gauge.set(len(running_gearman_jobs))


@skip_if_prometheus_disabled
def task_completed(task, task_group):
    if task.finished_timestamp is None:
        return

    group_name = task_group.linkTaskManager.jobChainLink.group
    task_name = task_group.linkTaskManager.jobChainLink.description
    timediff = task.finished_timestamp - task.start_timestamp
    duration = timediff.total_seconds()

    task_counter.labels(group_name, task_name).inc()
    task_success_timestamp.labels(group_name, task_name).set_to_current_time()
    task_duration_summary.labels(group_name, task_name).observe(duration)


@skip_if_prometheus_disabled
def task_failed(task, task_group):
    group_name = task_group.linkTaskManager.jobChainLink.group
    task_name = task_group.linkTaskManager.jobChainLink.description

    task_error_timestamp.labels(group_name, task_name).set_to_current_time()
    task_error_counter.labels(group_name, task_name).inc()
    task_counter.labels(group_name, task_name).inc()
