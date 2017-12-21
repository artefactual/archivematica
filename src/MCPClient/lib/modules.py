"""Modules are good for you."""

from ConfigParser import RawConfigParser
import logging
import os

from django.conf import settings as django_settings


logger = logging.getLogger('archivematica.mcp.client')


# This dict will map the names of the client scripts listed in the config file
# (typically MCPClient/lib/archivematicaClientModules) to the full paths to
# those scripts on disk.
supported_modules = {}


replacement_dict = {
    "%sharedPath%": django_settings.SHARED_DIRECTORY,
    "%clientScriptsDirectory%": django_settings.CLIENT_SCRIPTS_DIRECTORY,
}


def load_supported_modules_support(client_script, client_script_path):
    """Replace variables in ``client_script_path`` and confirm path."""
    for key, value in replacement_dict.items():
        client_script_path = client_script_path.replace(key, value)

    if not os.path.isfile(client_script_path):
        logger.error('Warning! Module can\'t find file, or relies on system'
                     ' path: {%s} %s', client_script, client_script_path)
    supported_modules[client_script] = client_script_path + ' '


def load_supported_modules(file, load_special_modules=True):
    """Populate the global `supported_modules` dict.

    The dictionary is populatede by parsing the MCPClient modules config file
    (typically MCPClient/lib/archivematicaClientModules).
    """
    supported_modules_config = RawConfigParser()
    supported_modules_config.read(file)
    for client_script, client_script_path in supported_modules_config.items(
            'supportedCommands'):
        load_supported_modules_support(client_script, client_script_path)
    if not load_special_modules:
        return
    for client_script, client_script_path in supported_modules_config.items(
            'supportedCommandsSpecial'):
        load_supported_modules_support(client_script, client_script_path)
