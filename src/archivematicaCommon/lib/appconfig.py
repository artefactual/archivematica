"""
Configuration helper for MCPServer, MCPClient and Dashboard, used in:

    - MCPClient/lib/settings/common.py
    - MCPServer/lib/settings/common.py
    - Dashboard/src/settings/base.py

Config. attributes are declared on those settings files and they can be defined
by a dictionary indicating the 'section', 'option' and 'type' to be parsed by
the Config class. They can also be defined by a list of the same type of
dictionary and, in that case, the first obtained value will be the one returned.
Alternatively, they can include the 'section' and a 'process_function' callback
where a specific parsing process can be defined. Those callbacks must accept the
current appconfig Config object and the section.
"""
from __future__ import absolute_import

from django.core.exceptions import ImproperlyConfigured

import six.moves.configparser as ConfigParser

from env_configparser import EnvConfigParser


class Config(object):
    """EnvConfigParser wrapper"""

    def __init__(self, env_prefix, attrs):
        self.config = EnvConfigParser(prefix=env_prefix)
        self.attrs = attrs

    INVALID_ATTR_MSG = (
        "Invalid attribute: %s. Make sure the entry in the"
        " attribute has all the fields needed (section, option,"
        " type)."
    )

    UNDEFINED_ATTR_MSG = "The following configuration attribute must be defined: %s."

    def read_defaults(self, fp):
        self.config.readfp(fp)

    def read_files(self, files):
        self.config.read(files)

    def get(self, attr, default=None):
        if attr not in self.attrs:
            raise ImproperlyConfigured(
                "Unknown attribute: %s. Make sure the "
                "attribute has been included in the "
                "attribute list." % attr
            )

        attr_opts = self.attrs[attr]
        if isinstance(attr_opts, list):
            return self.get_from_opts_list(attr, attr_opts, default=default)
        if all(k in attr_opts for k in ("section", "process_function")):
            return attr_opts["process_function"](self, attr_opts["section"])
        if not all(k in attr_opts for k in ("section", "option", "type")):
            raise ImproperlyConfigured(self.INVALID_ATTR_MSG % attr)

        getter = "get{}".format(
            "" if attr_opts["type"] == "string" else attr_opts["type"]
        )
        kwargs = {"section": attr_opts["section"], "option": attr_opts["option"]}
        if default is not None:
            kwargs["fallback"] = default
        elif "default" in attr_opts:
            kwargs["fallback"] = attr_opts["default"]

        try:
            return getattr(self.config, getter)(**kwargs)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            raise ImproperlyConfigured(self.UNDEFINED_ATTR_MSG % attr)

    def get_from_opts_list(self, attr, attr_opts_list, default=None):
        if not all(
            all(k in attr_opts for k in ("section", "option", "type"))
            for attr_opts in attr_opts_list
        ):
            raise ImproperlyConfigured(self.INVALID_ATTR_MSG % attr)
        for attr_opts in attr_opts_list:
            opt_type = attr_opts["type"]
            getter = "get{}".format({"string": ""}.get(opt_type, opt_type))
            kwargs = {"section": attr_opts["section"], "option": attr_opts["option"]}
            if default is not None:
                kwargs["fallback"] = default
            elif "default" in attr_opts:
                kwargs["fallback"] = attr_opts["default"]
            try:
                return getattr(self.config, getter)(**kwargs)
            except (
                ConfigParser.NoSectionError,
                ConfigParser.NoOptionError,
                ValueError,
            ):
                pass
        raise ImproperlyConfigured(self.UNDEFINED_ATTR_MSG % attr)


def process_search_enabled(config, section):
    """
    The 'search_enabled' attribute accepts four options and its value
    may be a boolean or a string containing a list of enabled parts
    separated by comma after it's obtained from the ConfigParser.
    This function normalizes and verifies the value to always return a list
    with the enabled parts. It may raise ImproperlyConfigured if the
    string value is empty or it contains an unrecognized search part.
    """
    ALLOWED_SEARCH_PARTS = set(["aips", "transfers"])
    options = [
        {
            "section": section,
            "option": "disableElasticsearchIndexing",
            "type": "iboolean",
        },
        {"section": section, "option": "disable_search_indexing", "type": "iboolean"},
        {"section": section, "option": "search_enabled", "type": "boolean"},
        {"section": section, "option": "search_enabled", "type": "string"},
    ]
    value = config.get_from_opts_list("search_enabled", options)
    if isinstance(value, bool):
        if value:
            return ALLOWED_SEARCH_PARTS
        else:
            return set()
    value = value.strip()
    if len(value) == 0:
        raise ImproperlyConfigured(config.UNDEFINED_ATTR_MSG % "search_enabled")
    enabled_parts = []
    for item in value.split(","):
        item = item.strip()
        if len(item) == 0:
            continue
        if item in ALLOWED_SEARCH_PARTS:
            enabled_parts.append(item)
        else:
            raise ImproperlyConfigured(
                '"%s" is not a recognized value for the search_enabled '
                'attribute. Only "aips" and/or "transfers" are allowed.' % item
            )
    return set(enabled_parts)


def process_watched_directory_interval(config, section):
    """Backward compatible lookup of watch_directory_interval."""
    options = [
        {"section": section, "option": "watch_directory_interval", "type": "int"},
        {"section": section, "option": "watchDirectoriesPollInterval", "type": "int"},
    ]

    return config.get_from_opts_list("watch_directory_interval", options, default=1)
