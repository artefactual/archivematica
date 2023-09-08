import importlib
import warnings
from configparser import RawConfigParser


def get_supported_modules(modules_file_path):
    """Create and return the ``supported_modules`` dict by parsing the MCPClient
    modules config file (typically MCPClient/lib/archivematicaClientModules).
    """
    supported_modules = {}
    supported_modules_config = RawConfigParser()
    supported_modules_config.read(modules_file_path)
    for client_script, module_name in supported_modules_config.items(
        "supportedBatchCommands"
    ):
        supported_modules[client_script] = module_name

    return supported_modules


def load_module(module_name):
    # No need to cache here as imports are already cached.
    try:
        return importlib.import_module(f"clientScripts.{module_name}")
    except ImportError as err:
        warnings.warn(
            f"Failed to load client script {module_name}: {err}",
            RuntimeWarning,
            stacklevel=2,
        )


def get_module_concurrency(module):
    if hasattr(module, "concurrent_instances"):
        return module.concurrent_instances()
    else:
        return 1


def load_job_modules(modules_file_path):
    """Return a dict of {client script name: module}."""
    supported_modules = get_supported_modules(modules_file_path)

    return dict(
        zip(supported_modules.keys(), map(load_module, supported_modules.values()))
    )
