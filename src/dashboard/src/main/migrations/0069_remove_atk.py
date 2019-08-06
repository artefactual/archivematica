# -*- coding: utf-8 -*-

"""Remove Archivists' Toolkit data and model."""
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


def data_migration_up(apps, _):
    SIPArrangeAccessMapping = apps.get_model("main", "SIPArrangeAccessMapping")
    SIPArrangeAccessMapping.objects.filter(system="atk").delete()

    DashboardSetting = apps.get_model("main", "DashboardSetting")
    DashboardSetting.objects.filter(scope="upload-archivistsToolkit_v0.0").delete()


class Migration(migrations.Migration):

    dependencies = [("main", "0068_version_number")]

    operations = [
        migrations.DeleteModel(name="AtkDIPObjectResourcePairing"),
        migrations.RunPython(data_migration_up, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="siparrangeaccessmapping",
            name="system",
            field=models.CharField(
                default="atom",
                max_length=255,
                choices=[("archivesspace", "ArchivesSpace"), ("atom", "AtoM")],
            ),
        ),
    ]
