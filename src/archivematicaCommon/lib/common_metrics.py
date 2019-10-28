import time
from contextlib import contextmanager

from prometheus_client import Counter

# We need to balance reasonably accurate tracking with high cardinality here, as
# this is used with script_name labels and there are already over 100 scripts.
TASK_DURATION_BUCKETS = (
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
    15.0,
    20.0,
    25.0,
    30.0,
    40.0,
    50.0,
    60.0,  # 1 min
    90.0,  # 1 min 30 sec
    120.0,  # 2 min
    180.0,  # 3 min
    300.0,  # 5 min
    450.0,  # 7.5 min
    600.0,  # 10 min
    900.0,  # 15 min
    1200.0,  # 20 min
    1800.0,  # 30 min
    2700.0,  # 45 min
    3600.0,  # 1 hour
    float("inf"),
)
# Histogram buckets for total processing time, e.g. for an AIP.
# Not used with labels.
PROCESSING_TIME_BUCKETS = (
    10.0,
    15.0,
    20.0,
    25.0,
    30.0,
    40.0,
    50.0,
    60.0,  # 1 min
    70.0,  # 1 min 10 sec
    80.0,  # 1 min 20 sec
    90.0,  # 1 min 30 sec
    100.0,  # 1 min 40 sec
    110.0,  # 1 min 50 sec
    120.0,  # 2 min
    135.0,  # 2 min 15 sec
    150.0,  # 2 min 30 sec
    165.0,  # 2 min 45 sec
    180.0,  # 3 min
    210.0,  # 2 min 30 sec
    240.0,  # 4 min
    270.0,  # 4 min 30 sec
    300.0,  # 5 min
    330.0,  # 5 min 30 sec
    360.0,  # 6 min
    390.0,  # 6 min 30 sec
    420.0,  # 7 min
    450.0,  # 7 min 30 sec
    480.0,  # 8 min
    510.0,  # 8 min 30 sec
    540.0,  # 9 min
    600.0,  # 10 min
    750.0,  # 12 min 30 sec
    900.0,  # 15 min
    1200.0,  # 20 min
    1500.0,  # 25 min
    1800.0,  # 30 min
    2400.0,  # 40 min
    3000.0,  # 50 min
    3600.0,  # 1 hour
    4500.0,  # 1 hour 15 min
    5400.0,  # 1 hour 30 min
    6300.0,  # 1 hour 45 min
    7200.0,  # 2 hours
    10800.0,  # 3 hours
    14400.0,  # 4 hours
    18000.0,  # 5 hours
    21600.0,  # 6 hours
    25200.0,  # 7 hours
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
