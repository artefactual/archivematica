# -*- coding: utf-8 -*-
from __future__ import absolute_import

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
    1800.0,  # 30 min
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
    1800.0,  # 30 min
    3600.0,  # 1 hour
    7200.0,  # 2 hours
    14400.0,  # 4 hours
    28800.0,  # 8 hours
    float("inf"),
)
# Histogram for distribution of transfer and AIP file counts
PACKAGE_FILE_COUNT_BUCKETS = (
    10.0,
    50.0,
    100.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    5000.0,
    10000.0,
    float("inf"),
)
# Histogram for distribution of transfer and AIP size in bytes
PACKAGE_SIZE_BUCKETS = (
    1000000.0,  # 1 MB
    10000000.0,  # 10 MB
    50000000.0,  # 50 MB
    100000000.0,  # 100 MB
    200000000.0,  # 200 MB
    500000000.0,  # 500 MB
    1000000000.0,  # 1 GB
    5000000000.0,  # 5 GB
    10000000000.0,  # 10 GB
    float("inf"),
)


db_retry_time_counter = Counter(
    "common_db_retry_time_seconds",
    (
        "Total time waiting to retry database transactions in seconds, labeled "
        "by operation description"
    ),
    ["description"],
)
ss_api_time_counter = Counter(
    "common_ss_api_request_duration_seconds",
    (
        "Total time waiting on the Storage Service API in seconds, labeled by "
        "function name"
    ),
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
