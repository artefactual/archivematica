"""
Exposes various metrics via Prometheus.
"""

import functools
import os

from django.conf import settings
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram
from prometheus_client import Info
from prometheus_client import start_http_server

from archivematica.archivematicaCommon.common_metrics import TASK_DURATION_BUCKETS
from archivematica.archivematicaCommon.version import get_full_version

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
transfer_start_active_gauge = Gauge(
    "mcpserver_transfer_start_active_tasks",
    "Number of transfer start tasks currently retrieving content from transfer sources",
)
transfer_start_queued_gauge = Gauge(
    "mcpserver_transfer_start_queued_tasks",
    "Number of transfer start tasks queued before retrieving content from transfer sources",
)
transfer_start_max_workers_gauge = Gauge(
    "mcpserver_transfer_start_max_workers",
    "Maximum number of transfer start tasks that may run concurrently",
)
transfer_start_counter = Counter(
    "mcpserver_transfer_start_total",
    "Number of transfer start tasks, labeled by outcome",
    ["status"],
)
transfer_start_duration_histogram = Histogram(
    "mcpserver_transfer_start_duration_seconds",
    "Duration of transfer start tasks in seconds, labeled by outcome",
    ["status"],
    buckets=TASK_DURATION_BUCKETS,
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
def configure_transfer_start_executor(max_workers):
    transfer_start_max_workers_gauge.set(max_workers)
    transfer_start_active_gauge.set(0)
    transfer_start_queued_gauge.set(0)
    for status in ("submitted", "succeeded", "failed"):
        transfer_start_counter.labels(status=status)
    for status in ("succeeded", "failed"):
        transfer_start_duration_histogram.labels(status=status)


@skip_if_prometheus_disabled
def transfer_start_submitted():
    transfer_start_queued_gauge.inc()
    transfer_start_counter.labels(status="submitted").inc()


@skip_if_prometheus_disabled
def transfer_start_running():
    transfer_start_queued_gauge.dec()
    transfer_start_active_gauge.inc()


@skip_if_prometheus_disabled
def transfer_start_finished(status, duration):
    transfer_start_active_gauge.dec()
    transfer_start_counter.labels(status=status).inc()
    transfer_start_duration_histogram.labels(status=status).observe(duration)


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
