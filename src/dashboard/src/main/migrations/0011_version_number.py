# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    Agent = apps.get_model("main", "Agent")
    Agent.objects.filter(
        identifiertype="preservation system", name="Archivematica"
    ).update(identifiervalue="Archivematica-1.5.0")


class Migration(migrations.Migration):

    dependencies = [("main", "0010_dip_upload_store")]

    operations = [migrations.RunPython(data_migration)]
