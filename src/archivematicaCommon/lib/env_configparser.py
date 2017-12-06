from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
import os
import configparser
import functools


def fallback_option(fn):
    def wrapper(*args, **kwargs):
        fallback = kwargs.pop('fallback', None)
        try:
            return fn(*args, **kwargs)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback:
                return fallback
            raise
    return functools.wraps(fn)(wrapper)


class EnvConfigParser(configparser.SafeConfigParser):
    """
    EnvConfigParser enables the user to provide configuration defaults using
    the string environment, e.g. given:

      - String environment prefix (prefix) = "ARCHIVEMATICA_MCPSERVER"
      - Configuration section: "network"
      - Configuration option: "tls"

    This parser will first try to find the configuration value in the string
    environment matching one of the two following keys:

      - ARCHIVEMATICA_MCPSERVER_NETWORK_TLS
      - ARCHIVEMATICA_MCPSERVER_TLS

    If the variable is not set in the string environment the reader falls back
    on the main configuration backend.

    Additionally, the getters (get(), getint(), etc...) accept a new parameter
    (fallback) that returns the value given to it instead of an exception when
    the section or option trying to be match are undefined.
    """
    ENVVAR_SEPARATOR = '_'

    def __init__(self, defaults=None, env=None, prefix=''):
        self._environ = env or os.environ
        self._prefix = prefix.rstrip('_')
        configparser.SafeConfigParser.__init__(self, defaults)

    def _get_envvar(self, section, option):
        for key in (
            self.ENVVAR_SEPARATOR.join([self._prefix, section, option]).upper(),
            self.ENVVAR_SEPARATOR.join([self._prefix, option]).upper(),
        ):
            if key in self._environ:
                return self._environ[key]

    @fallback_option
    def get(self, section, option, **kwargs):
        ret = self._get_envvar(section, option)
        if ret:
            return ret
        return configparser.SafeConfigParser.get(self, section, option, **kwargs)

    @fallback_option
    def getint(self, *args, **kwargs):
        return configparser.SafeConfigParser.getint(self, *args, **kwargs)

    @fallback_option
    def getfloat(self, *args, **kwargs):
        return configparser.SafeConfigParser.getfloat(self, *args, **kwargs)

    @fallback_option
    def getboolean(self, *args, **kwargs):
        return configparser.SafeConfigParser.getboolean(self, *args, **kwargs)
