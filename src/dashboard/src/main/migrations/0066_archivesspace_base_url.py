# -*- coding: utf-8 -*-

"""Migrate the ArchivesSpace connection details.

``host`` and `port`` are replaced by ``base_url``.
"""
from __future__ import absolute_import, unicode_literals

from six.moves.urllib.parse import urlparse

from django.db import migrations

_AS_DICTNAME = "upload-archivesspace_v0.0"

_AS_UPLOAD_STC = "10a0f352-aeb7-4c13-8e9e-e81bda9bca29"


def _load_config(DashboardSetting):
    """Load the ArchivesSpace configuration dictionary."""
    return DashboardSetting.objects.get_dict(_AS_DICTNAME)


def _save_config(DashboardSetting, params):
    """Set the ArchivesSpace configuration dictionary."""
    DashboardSetting.objects.set_dict(_AS_DICTNAME, params)


def _get_base_url(host, port):
    """Convert ``host`` and ``port`` to ``base_url``.

    So the user does not need to tweak the settings during upgrades.
    See ``test_migrations.py`` for to understand the behaviour.
    """
    try:
        parsed = urlparse(host)
    except AttributeError:
        pass
    else:
        if parsed.scheme:
            return parsed.geturl()
    if not host:
        return ""
    parts = host.partition(":")
    host = parts[0]
    if parts[1] == ":":
        return "http://{}:{}".format(host, parts[2])
    try:
        port = int(port)
    except (ValueError, TypeError):
        pass
    else:
        return "http://{}:{}".format(host, port)
    return "http://{}".format(host)


def _get_host_and_port(base_url):
    """Convert ``base_url`` back to ``host`` and ``port``.

    It is a losing game, only best effort.
    See ``test_migrations.py`` for to understand the behaviour.
    """
    base_url = base_url or ""
    host, port = "", ""
    try:
        base_url = urlparse(base_url)
    except AttributeError:
        return host, port
    host = base_url.netloc
    if not host:
        host = base_url.path
    parts = host.partition(":")
    if parts[1] == ":":
        host, port = parts[0], parts[2]
    return host, port


def data_migration_up(apps, schema_editor):
    """Restore `base_url`."""
    DashboardSetting = apps.get_model("main", "DashboardSetting")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")

    config = _load_config(DashboardSetting)
    host, port = config.pop("host", None), config.pop("port", None)
    config["base_url"] = _get_base_url(host, port)
    _save_config(DashboardSetting, config)

    # Use new command-line arguments ``--base-url``.
    StandardTaskConfig.objects.filter(
        id=_AS_UPLOAD_STC, execute="upload-archivesspace_v0.0"
    ).update(
        arguments='--base-url "%base_url%" '
        '--user "%user%" '
        '--passwd "%passwd%" '
        '--dip_location "%SIPDirectory%" '
        '--dip_name "%SIPName%" '
        '--dip_uuid "%SIPUUID%" '
        '--restrictions "%restrictions%" '
        '--object_type "%object_type%" '
        '--xlink_actuate "%xlink_actuate%" '
        '--xlink_show "%xlink_show%" '
        '--use_statement "%use_statement%" '
        '--uri_prefix "%uri_prefix%" '
        '--access_conditions "%access_conditions%" '
        '--use_conditions "%use_conditions%" '
        '--inherit_notes "%inherit_notes%"'
    )


def data_migration_down(apps, schema_editor):
    """Restore `host` and `port`."""
    DashboardSetting = apps.get_model("main", "DashboardSetting")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")

    config = _load_config(DashboardSetting)
    base_url = config.pop("base_url", None)
    config["host"], config["port"] = _get_host_and_port(base_url)
    _save_config(DashboardSetting, config)

    # Restore previous command-line arguments ``--host`` and ``--port``.
    StandardTaskConfig.objects.filter(
        id=_AS_UPLOAD_STC, execute="upload-archivesspace_v0.0"
    ).update(
        arguments='--host "%host%" '
        '--port "%port%" '
        '--user "%user%" '
        '--passwd "%passwd%" '
        '--dip_location "%SIPDirectory%" '
        '--dip_name "%SIPName%" '
        '--dip_uuid "%SIPUUID%" '
        '--restrictions "%restrictions%" '
        '--object_type "%object_type%" '
        '--xlink_actuate "%xlink_actuate%" '
        '--xlink_show "%xlink_show%" '
        '--use_statement "%use_statement%" '
        '--uri_prefix "%uri_prefix%" '
        '--access_conditions "%access_conditions%" '
        '--use_conditions "%use_conditions%" '
        '--inherit_notes "%inherit_notes%"'
    )


class Migration(migrations.Migration):
    dependencies = [("main", "0065_version_number")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
