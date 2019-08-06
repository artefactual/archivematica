# -*- coding: utf-8 -*-
"""Migration to ensure that if extract contents from compressed archives
fails that the workflow doesn't continue to trudge along to completion where
there is a likelihood of other errors.
"""
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration_down(apps, schema_editor):
    """Reset the two fields in the Dashboard data model for the two affected
    transfer types.
    """
    std_transfer_extract_packages_link = "1cb7e228-6e94-4c93-bf70-430af99b9264"
    dspace_extract_packages_link = "bd792750-a55b-42e9-903a-8c898bb77df1"
    original_failed_transfer_link = "307edcde-ad10-401c-92c4-652917c993ed"
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLink.objects.filter(id=dspace_extract_packages_link).update(
        defaultnextchainlink=original_failed_transfer_link
    )
    MicroServiceChainLink.objects.filter(id=std_transfer_extract_packages_link).update(
        defaultnextchainlink=original_failed_transfer_link
    )


def data_migration_up(apps, schema_editor):
    """Update two fields in the Dashboard data model for the two affected
    transfer types.
    """
    std_transfer_extract_packages_link = "1cb7e228-6e94-4c93-bf70-430af99b9264"
    dspace_extract_packages_link = "bd792750-a55b-42e9-903a-8c898bb77df1"
    new_failed_transfer_link = "61c316a6-0a50-4f65-8767-1f44b1eeb6dd"
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLink.objects.filter(id=dspace_extract_packages_link).update(
        defaultnextchainlink=new_failed_transfer_link
    )
    MicroServiceChainLink.objects.filter(id=std_transfer_extract_packages_link).update(
        defaultnextchainlink=new_failed_transfer_link
    )


class Migration(migrations.Migration):
    """Entry point for the migration."""

    dependencies = [("main", "0051_remove_verify_premis_checksums")]
    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
