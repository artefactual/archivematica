import time
from contextlib import contextmanager

from prometheus_client import Counter

# We need to balance reasonably accurate tracking with high cardinality here, as
# this is used with script_name labels and there are already over 100 scripts.
TASK_DURATION_BUCKETS = (
    2.0,
    5.0,
    10.0,
    20.0,
    30.0,
    60.0,
    120.0,  # 2 min
    300.0,  # 5 min
    600.0,  # 10 min
    1500.0,  # 30 min
    3600.0,  # 1 hour
    float("inf"),
)
# Histogram buckets for total processing time, e.g. for an AIP.
# Not used with labels.
PROCESSING_TIME_BUCKETS = (
    10.0,
    20.0,
    30.0,
    60.0,
    120.0,  # 2 min
    300.0,  # 5 min
    600.0,  # 10 min
    1500.0,  # 30 min
    3600.0,  # 1 hour
    7200.0,  # 2 hours
    14400.0,  # 4 hours
    28800.0,  # 8 hours
    float("inf"),
)


db_retry_time_counter = Counter(
    "common_db_retry_time_seconds",
    "Total time waiting to retry database transactions in seconds",
    ["description"],
)
ss_api_time_counter = Counter(
    "common_ss_api_request_duration_seconds",
    "Total time waiting on the Storage Service API in seconds",
    ["function"],
)


@contextmanager
def db_retry_timer(*args, **kwargs):
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        db_retry_time_counter.labels(**kwargs).inc(duration)


@contextmanager
def ss_api_timer(*args, **kwargs):
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        ss_api_time_counter.labels(**kwargs).inc(duration)
