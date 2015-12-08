try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os
import logging

from config import settings, LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('archivematica.mcp.client')


replacement_dict = {
    "%sharedPath%": settings.get('MCPClient', 'shared_directory'),
    "%clientScriptsDirectory%": settings.get('MCPClient', 'client_scripts_directory')
}


def _load_modules():
    modules_config = configparser.RawConfigParser()
    modules_config.read(settings.get('MCPClient', 'modules_file'))
    modules = {}

    # Load regular modules
    for key, value in modules_config.items('supportedCommands'):
        modules[key] = _interpolate_module_value(value)

    # Load special modules
    load_special_scripts = settings.getboolean('MCPClient', 'load_special_scripts')
    if load_special_scripts:
        for key, value in modules_config.items('supportedCommandsSpecial'):
            modules[key] = _interpolate_module_value(value)

    # Report if the module cannot be found
    for key, value in modules.iteritems():
        if not os.path.isfile(value):
            logger.error('Warning! Module %s could not be found: %s', key, value)

    return modules


def _interpolate_module_value(value):
    for k, v in replacement_dict.iteritems():
        value = value.replace(k, v)
    return value + " "


supported_modules = _load_modules()
