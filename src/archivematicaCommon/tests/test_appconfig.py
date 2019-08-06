# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from django.core.exceptions import ImproperlyConfigured
import pytest
from six import StringIO

from appconfig import Config, process_search_enabled


CONFIG_MAPPING = {
    "search_enabled": {
        "section": "Dashboard",
        "process_function": process_search_enabled,
    }
}


@pytest.mark.parametrize(
    "option, value, expect",
    [
        ("search_enabled", "true", ["aips", "transfers"]),
        ("search_enabled", "false", []),
        ("search_enabled", " ", ImproperlyConfigured),
        ("search_enabled", "aips", ["aips"]),
        ("search_enabled", "transfers", ["transfers"]),
        ("search_enabled", "aips,transfers", ["aips", "transfers"]),
        ("search_enabled", "aips, transfers", ["aips", "transfers"]),
        ("search_enabled", "unknown", ImproperlyConfigured),
        ("search_enabled", "aips,unknown", ImproperlyConfigured),
        ("disable_search_indexing", "true", []),
        ("disable_search_indexing", "false", ["aips", "transfers"]),
    ],
)
def test_mapping_list_config_file(option, value, expect):
    config = Config(env_prefix="ARCHIVEMATICA_DASHBOARD", attrs=CONFIG_MAPPING)
    config.read_defaults(
        StringIO(
            "[Dashboard]\n" "{option} = {value}".format(option=option, value=value)
        )
    )
    if isinstance(expect, list):
        assert sorted(config.get("search_enabled")) == sorted(expect)
    else:
        with pytest.raises(expect):
            config.get("search_enabled")


@pytest.mark.parametrize(
    "envvars, expect",
    [
        (
            {"ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED": "true"},
            ["aips", "transfers"],
        ),
        ({"ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED": "false"}, []),
        ({"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "true"}, ["aips", "transfers"]),
        ({"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "false"}, []),
        ({"ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING": "true"}, []),
        (
            {"ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING": "false"},
            ["aips", "transfers"],
        ),
        ({"ARCHIVEMATICA_DASHBOARD_DISABLE_SEARCH_INDEXING": "true"}, []),
        (
            {"ARCHIVEMATICA_DASHBOARD_DISABLE_SEARCH_INDEXING": "false"},
            ["aips", "transfers"],
        ),
        ({"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": ""}, ImproperlyConfigured),
        ({"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "aips"}, ["aips"]),
        ({"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "transfers"}, ["transfers"]),
        (
            {"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "aips,transfers"},
            ["aips", "transfers"],
        ),
        (
            {"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "unknown,transfers"},
            ImproperlyConfigured,
        ),
        ({}, ImproperlyConfigured),
        # Following two show that the DISABLE env var overrides the ENABLE one
        # because of the ordering in CONFIG_MAPPING.
        (
            {
                "ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED": "aips",
                "ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING": "true",
            },
            [],
        ),
        (
            {
                "ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED": "false",
                "ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING": "false",
            },
            ["aips", "transfers"],
        ),
    ],
)
def test_mapping_list_env_var(envvars, expect):
    for var, val in envvars.items():
        os.environ[var] = val
    config = Config(env_prefix="ARCHIVEMATICA_DASHBOARD", attrs=CONFIG_MAPPING)
    if isinstance(expect, list):
        assert sorted(config.get("search_enabled")) == sorted(expect)
    else:
        with pytest.raises(expect):
            config.get("search_enabled")
    for var in envvars:
        del os.environ[var]
