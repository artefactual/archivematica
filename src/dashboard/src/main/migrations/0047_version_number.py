# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    Agent = apps.get_model("main", "Agent")
    Agent.objects.filter(
        identifiertype="preservation system", name="Archivematica"
    ).update(identifiervalue="Archivematica-1.7")


class Migration(migrations.Migration):

    dependencies = [("main", "0046_optional_normative_structmap")]

    operations = [migrations.RunPython(data_migration)]
