import os


def configure_prometheus_client() -> None:
    """Keep MCPClient metrics in the parent-owned scrape contract.

    Some client script imports can load prometheus_client before this package is
    imported. Resetting ValueClass after clearing the environment keeps later
    MCPClient collectors in normal in-process mode even in that import order.
    Created-series export is also disabled so normal collectors do not add
    time series that the previous MultiProcessCollector scrape did not expose.
    """
    os.environ.pop("PROMETHEUS_MULTIPROC_DIR", None)
    os.environ.pop("prometheus_multiproc_dir", None)
    os.environ["PROMETHEUS_DISABLE_CREATED_SERIES"] = "true"
    from prometheus_client import disable_created_metrics
    from prometheus_client import values

    disable_created_metrics()
    values.ValueClass = values.get_value_class()


# MCPClient owns Prometheus metrics in the parent process. Workers send metric
# events to the parent over a multiprocessing queue instead of using
# prometheus_client multiprocess mode, which stores per-worker mmap files that
# grow without bound when workers are recycled frequently.
configure_prometheus_client()
