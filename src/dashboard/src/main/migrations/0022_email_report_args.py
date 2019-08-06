# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    # Delete `date` and `server` arguments as they are not needed
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    StandardTaskConfig.objects.filter(execute="emailFailReport_v0.0").update(
        arguments='--unitType "%unitType%" --unitIdentifier "%SIPUUID%" --unitName "%SIPName%"'
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0021_checksum_algorithms")]

    operations = [migrations.RunPython(data_migration)]
