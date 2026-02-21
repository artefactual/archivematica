import os
from io import StringIO

import pytest
from django.core.exceptions import ImproperlyConfigured

from archivematica.archivematicaCommon.appconfig import Config
from archivematica.archivematicaCommon.appconfig import process_search_enabled

CONFIG_MAPPING = {
    "search_enabled": {
        "section": "Dashboard",
        "process_function": process_search_enabled,
    }
}


@pytest.mark.parametrize(
    "option, value, expect, warn_deprecated",
    [
        ("search_enabled", "true", ["aips"], False),
        ("search_enabled", "false", [], False),
        ("search_enabled", " ", ImproperlyConfigured, False),
        ("search_enabled", "aips", ["aips"], False),
        ("search_enabled", "transfers", [], True),
        ("search_enabled", "aips,transfers", ["aips"], True),
        ("search_enabled", "aips, transfers", ["aips"], True),
        ("search_enabled", "unknown", ImproperlyConfigured, False),
        ("search_enabled", "aips,unknown", ImproperlyConfigured, False),
        ("disable_search_indexing", "true", [], False),
        ("disable_search_indexing", "false", ["aips"], False),
    ],
)
def test_mapping_list_config_file(option, value, expect, warn_deprecated, caplog):
    config = Config(env_prefix="ARCHIVEMATICA_DASHBOARD", attrs=CONFIG_MAPPING)
    config.read_defaults(StringIO(f"[Dashboard]\n{option} = {value}"))
    caplog.clear()
    if isinstance(expect, list):
        assert sorted(config.get("search_enabled")) == sorted(expect)
        warning_messages = [record.message for record in caplog.records]
        has_warning = any(
            "Ignoring deprecated search_enabled value(s): transfers." in message
            for message in warning_messages
        )
        assert has_warning is warn_deprecated
    else:
        with pytest.raises(expect):
            config.get("search_enabled")


@pytest.mark.parametrize(
    "envvars, expect, warn_deprecated",
    [
        (
            {"ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED": "true"},
            ["aips"],
            False,
        ),
        ({"ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED": "false"}, [], False),
        ({"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "true"}, ["aips"], False),
        ({"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "false"}, [], False),
        (
            {"ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING": "true"},
            [],
            False,
        ),
        (
            {"ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING": "false"},
            ["aips"],
            False,
        ),
        ({"ARCHIVEMATICA_DASHBOARD_DISABLE_SEARCH_INDEXING": "true"}, [], False),
        (
            {"ARCHIVEMATICA_DASHBOARD_DISABLE_SEARCH_INDEXING": "false"},
            ["aips"],
            False,
        ),
        ({"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": ""}, ImproperlyConfigured, False),
        ({"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "aips"}, ["aips"], False),
        (
            {"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "transfers"},
            [],
            True,
        ),
        (
            {"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "aips,transfers"},
            ["aips"],
            True,
        ),
        (
            {"ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED": "unknown,transfers"},
            ImproperlyConfigured,
            False,
        ),
        ({}, ImproperlyConfigured, False),
        # Following two show that the DISABLE env var overrides the ENABLE one
        # because of the ordering in CONFIG_MAPPING.
        (
            {
                "ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED": "aips",
                "ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING": "true",
            },
            [],
            False,
        ),
        (
            {
                "ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED": "false",
                "ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING": "false",
            },
            ["aips"],
            False,
        ),
    ],
)
def test_mapping_list_env_var(envvars, expect, warn_deprecated, caplog):
    for var, val in envvars.items():
        os.environ[var] = val
    try:
        config = Config(env_prefix="ARCHIVEMATICA_DASHBOARD", attrs=CONFIG_MAPPING)
        caplog.clear()
        if isinstance(expect, list):
            assert sorted(config.get("search_enabled")) == sorted(expect)
            warning_messages = [record.message for record in caplog.records]
            has_warning = any(
                "Ignoring deprecated search_enabled value(s): transfers." in message
                for message in warning_messages
            )
            assert has_warning is warn_deprecated
        else:
            with pytest.raises(expect):
                config.get("search_enabled")
    finally:
        for var in envvars:
            del os.environ[var]
