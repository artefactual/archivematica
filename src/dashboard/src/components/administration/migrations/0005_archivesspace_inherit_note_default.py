# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    # Insert default values into the ArchivesSpaceConfig table.
    # Leaving all other values null/blank is consistent with default ATK config.
    ArchivesSpaceConfig = apps.get_model("administration", "ArchivesSpaceConfig")
    ArchivesSpaceConfig.objects.filter(
        id="5e6b9fb2-0ed0-41c4-b5cb-94d25de1a5dc"
    ).update(inherit_notes=False)


class Migration(migrations.Migration):

    dependencies = [("administration", "0004_archivesspaceconfig_inherit_notes")]

    operations = [migrations.RunPython(data_migration)]
