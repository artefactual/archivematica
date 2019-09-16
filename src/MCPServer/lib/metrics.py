"""
Exposes various metrics via Prometheus.
"""
from __future__ import absolute_import, unicode_literals

import functools

from django.conf import settings
from prometheus_client import Counter, Gauge, Summary


active_task_group_gauge = Gauge(
    "archivematica_active_task_groups",
    "Number of task groups currently being processed",
)
gearman_active_jobs_gauge = Gauge(
    "archivematica_gearman_active_jobs",
    "Number of gearman jobs currently being processed",
)
gearman_pending_jobs_gauge = Gauge(
    "archivematica_gearman_pending_jobs", "Number of gearman jobs pending submission"
)
task_counter = Counter(
    "archivematica_task_total",
    "Number of tasks processed",
    ["task_group_name", "task_name"],
)
task_error_counter = Counter(
    "archivematica_task_error_total",
    "Number of failures processing tasks",
    ["task_group_name", "task_name"],
)
task_success_timestamp = Gauge(
    "archivematica_task_success_timestamp",
    "Most recent successfully processed task",
    ["task_group_name", "task_name"],
)
task_error_timestamp = Gauge(
    "archivematica_task_error_timestamp",
    "Most recent failure when processing a task",
    ["task_group_name", "task_name"],
)
task_duration_summary = Summary(
    "archivematica_task_duration_seconds",
    "Summary of task durations in seconds",
    ["task_group_name", "task_name"],
)
aips_stored_counter = Counter(
    "archivematica_aips_stored_total", "Number of AIPs stored"
)


def skip_if_prometheus_disabled(func):
    @functools.wraps(func)
    def wrapper(*args, **kwds):
        if settings.PROMETHEUS_HTTP_SERVER:
            return func(*args, **kwds)
        return None

    return wrapper


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

    # TODO: this is not a great way to measure AIP storage time - this should
    # be tracked elsewhere (possibly in Storage Service)
    if task_group.execute == "storeAIP_v0.0":
        aips_stored_counter.inc()


@skip_if_prometheus_disabled
def task_failed(task, task_group):
    group_name = task_group.linkTaskManager.jobChainLink.group
    task_name = task_group.linkTaskManager.jobChainLink.description

    task_error_timestamp.labels(group_name, task_name).set_to_current_time()
    task_error_counter.labels(group_name, task_name).inc()
    task_counter.labels(group_name, task_name).inc()
