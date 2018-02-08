from __future__ import absolute_import
import os
import StringIO

from django.core.exceptions import ImproperlyConfigured
import pytest

from appconfig import Config


CONFIG_MAPPING = {
    'search_enabled': [
        {'section': 'Dashboard', 'option': 'disable_search_indexing', 'type': 'iboolean'},
        {'section': 'Dashboard', 'option': 'search_enabled', 'type': 'boolean'},
    ],
}


@pytest.mark.parametrize('option, value, expect', [
    ('search_enabled', 'true', True),
    ('search_enabled', 'false', False),
    ('disable_search_indexing', 'true', False),
    ('disable_search_indexing', 'false', True),
])
def test_mapping_list_config_file(option, value, expect):
    config = Config(env_prefix='ARCHIVEMATICA_DASHBOARD', attrs=CONFIG_MAPPING)
    config.read_defaults(StringIO.StringIO(
        '[Dashboard]\n'
        '{option} = {value}'.format(option=option, value=value)))
    assert config.get('search_enabled') is expect


@pytest.mark.parametrize('envvars, expect', [
    ({'ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED': 'true'}, True),
    ({'ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED': 'false'}, False),
    ({'ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED': 'true'}, True),
    ({'ARCHIVEMATICA_DASHBOARD_SEARCH_ENABLED': 'false'}, False),
    ({'ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING': 'true'},
     False),
    ({'ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING': 'false'},
     True),
    ({'ARCHIVEMATICA_DASHBOARD_DISABLE_SEARCH_INDEXING': 'true'}, False),
    ({'ARCHIVEMATICA_DASHBOARD_DISABLE_SEARCH_INDEXING': 'false'}, True),
    ({}, ImproperlyConfigured),
    # Following two show that the DISABLE env var overrides the ENABLE one
    # because of the ordering in CONFIG_MAPPING.
    ({'ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED': 'true',
      'ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING': 'true'},
     False),
    ({'ARCHIVEMATICA_DASHBOARD_DASHBOARD_SEARCH_ENABLED': 'false',
      'ARCHIVEMATICA_DASHBOARD_DASHBOARD_DISABLE_SEARCH_INDEXING': 'false'},
     True),
])
def test_mapping_list_env_var(envvars, expect):
    for var, val in envvars.items():
        os.environ[var] = val
    config = Config(env_prefix='ARCHIVEMATICA_DASHBOARD', attrs=CONFIG_MAPPING)
    if bool(expect) is expect:
        search_enabled = config.get('search_enabled')
        assert search_enabled is expect
    else:
        with pytest.raises(expect):
            config.get('search_enabled')
    for var in envvars:
        del os.environ[var]
