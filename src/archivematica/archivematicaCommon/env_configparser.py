import configparser
import functools
import os


def fallback_option(fn):
    def wrapper(*args, **kwargs):
        fallback = kwargs.pop("fallback", None)
        try:
            return fn(*args, **kwargs)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback:
                return fallback
            raise

    return functools.wraps(fn)(wrapper)


class EnvConfigParser(configparser.RawConfigParser):
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

    ENVVAR_SEPARATOR = "_"

    def __init__(self, defaults=None, env=None, prefix=""):
        self._environ = env or os.environ
        self._prefix = prefix.rstrip("_")
        kwargs = {}
        kwargs["inline_comment_prefixes"] = (";",)
        super().__init__(defaults, **kwargs)

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
        return super().get(section, option, **kwargs)

    @fallback_option
    def getint(self, *args, **kwargs):
        return super().getint(*args, **kwargs)

    @fallback_option
    def getfloat(self, *args, **kwargs):
        return super().getfloat(*args, **kwargs)

    @fallback_option
    def getboolean(self, *args, **kwargs):
        return super().getboolean(*args, **kwargs)

    @fallback_option
    def getiboolean(self, *args, **kwargs):
        return not self.getboolean(*args, **kwargs)
