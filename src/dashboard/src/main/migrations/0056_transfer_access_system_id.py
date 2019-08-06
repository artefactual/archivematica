# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


def data_migration_up(apps, schema_editor):
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    TaskConfig = apps.get_model("main", "TaskConfig")
    MicroServiceChain.objects.filter(description="Upload DIP to AtoM").update(
        description="Upload DIP to AtoM/Binder"
    )
    TaskConfig.objects.filter(description="Choose config for AtoM DIP upload").update(
        description="Choose config for AtoM/Binder DIP upload"
    )


def data_migration_down(apps, schema_editor):
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    TaskConfig = apps.get_model("main", "TaskConfig")
    MicroServiceChain.objects.filter(description="Upload DIP to AtoM/Binder").update(
        description="Upload DIP to AtoM"
    )
    TaskConfig.objects.filter(
        description="Choose config for AtoM/Binder DIP upload"
    ).update(description="Choose config for AtoM DIP upload")


class Migration(migrations.Migration):

    dependencies = [("main", "0055_normalize_thumbnail_mode_selection")]

    operations = [
        migrations.AddField(
            model_name="transfer",
            name="access_system_id",
            field=models.TextField(default="", db_column="access_system_id"),
            preserve_default=False,
        ),
        migrations.RunPython(data_migration_up, data_migration_down),
    ]
