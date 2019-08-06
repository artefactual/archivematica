# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    Agent = apps.get_model("main", "Agent")
    Agent.objects.filter(
        identifiertype="preservation system", name="Archivematica"
    ).update(identifiervalue="Archivematica-1.6.0")


class Migration(migrations.Migration):

    dependencies = [("main", "0027_full_reingest")]

    operations = [migrations.RunPython(data_migration)]
