# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration_down(apps, _):
    Agent = apps.get_model("main", "Agent")
    Agent.objects.create(
        pk=1,
        identifiertype="preservation system",
        identifiervalue="Archivematica-1.13",
        name="Archivematica",
        agenttype="software",
    )


def data_migration_up(apps, _):
    Agent = apps.get_model("main", "Agent")
    Agent.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    """Run the migration to update the Archivematica agent version string."""

    dependencies = [("main", "0079_version_number")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
