# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations


def data_migration(apps, schema_editor):
    File = apps.get_model("main", "File")
    DashboardSetting = apps.get_model("main", "DashboardSetting")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")

    File.objects.filter(checksumtype="").update(checksumtype="sha256")
    DashboardSetting.objects.create(name="checksum_type", value="sha256")
    StandardTaskConfig.objects.filter(id="045f84de-2669-4dbc-a31b-43a4954d0481").update(
        arguments='create "%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPDirectory%" "logs/" "objects/" "METS.%SIPUUID%.xml" "thumbnails/" "metadata/" --writer filesystem'
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0020_index_after_processing_decision")]

    operations = [
        migrations.AddField(
            model_name="file",
            name="checksumtype",
            field=models.CharField(max_length=36, db_column="checksumType", blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="file",
            name="checksum",
            field=models.CharField(max_length=128, db_column="checksum", blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(data_migration),
    ]
