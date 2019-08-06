# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Migration 0032 inadvertently set previously non-existent "Upload DIP to
    AtoM" values to 'None'. This fixes that.
    """
    apps.get_model("main", "DashboardSetting").objects.filter(
        scope="upload-qubit_v0.0", value="None"
    ).update(value="")


class Migration(migrations.Migration):

    dependencies = [("main", "0047_version_number")]

    operations = [migrations.RunPython(data_migration)]
