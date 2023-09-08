import atexit
import os
import shutil
import tempfile


def configure_prometheus_multiproc_dir():
    """Create the Prometheus multi-process directory.

    Ensure that the multi-process directory exists. Use a temporary directory
    instead when the user did not provide one via the environment string.
    The environment string is always set for the library to be set up properly.
    """
    try:
        prometheus_tmp_dir = os.environ["PROMETHEUS_MULTIPROC_DIR"]
    except KeyError:
        pass
    else:
        os.makedirs(prometheus_tmp_dir, mode=0o770, exist_ok=True)
        return prometheus_tmp_dir

    prometheus_tmp_dir = tempfile.mkdtemp(prefix="prometheus-stats")
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = prometheus_tmp_dir

    return prometheus_tmp_dir


def delete_prometheus_multiproc_dir(prometheus_tmp_dir):
    """The multi-process directory must be wiped between runs."""
    shutil.rmtree(prometheus_tmp_dir)


# Set up the temporary directory that the Prometheus client library will use to
# store metrics of MCPClient and its child processes.
#
# Setting the environment string "prometheus_multiproc_dir" is the only
# mechanism we have to ensure that the Prometheus client library is in
# multi-process mode. "prometheus_client.values.ValueClass" will be an instance
# of "MultiProcessValue".
#
# This needs to happen before we import client.metrics. The temporary directory
# is removed before the application exits.
prometheus_tmp_dir = configure_prometheus_multiproc_dir()
atexit.register(delete_prometheus_multiproc_dir, prometheus_tmp_dir)
