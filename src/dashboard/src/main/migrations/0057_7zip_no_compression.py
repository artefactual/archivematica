# -*- coding: utf-8 -*-
"""Migration to add a 7-zip method to the list of Archivematica AIP 7-zip
methods that does not use compression. 7-zip copy mode.
"""
from __future__ import absolute_import, unicode_literals

from django.db import migrations

choice_no_compression_uuid = "e3906da0-41fb-4cb8-a598-6c73981b63e9"


def get_chain_choice_dict(apps):
    """Retrieve Chain Choice Replacement Dict model."""
    return apps.get_model("main", "MicroServiceChoiceReplacementDic")


def get_ms_chain_link_instance(apps, ms_uuid):
    """Get chainlink instance from the database."""
    return apps.get_model("main", "MicroServiceChainLink").objects.get(id=ms_uuid)


def data_migration_down(apps, schema_editor):
    get_chain_choice_dict(apps).objects.filter(id=choice_no_compression_uuid).delete()


def data_migration_up(apps, schema_editor):
    ms_prepare_aip = get_ms_chain_link_instance(
        apps, "01d64f58-8295-4b7b-9cab-8f1b153a504f"
    )
    get_chain_choice_dict(apps).objects.create(
        id=choice_no_compression_uuid,
        description="7z without compression (Copy)",
        replacementdic='{"%AIPCompressionAlgorithm%":"7z-copy"}',
        choiceavailableatlink=ms_prepare_aip,
    )


class Migration(migrations.Migration):
    """Entry point for the migration."""

    dependencies = [("main", "0056_transfer_access_system_id")]
    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
