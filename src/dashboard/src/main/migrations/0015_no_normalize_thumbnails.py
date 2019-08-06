# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    # Do not Normalize generate thumbnails should use original not service
    StandardTaskConfig.objects.filter(id="26309e7d-6435-4700-9171-131005f29cbb").update(
        arguments='thumbnail "%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%" "original"'
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0014_aic_fixes")]

    operations = [migrations.RunPython(data_migration)]
