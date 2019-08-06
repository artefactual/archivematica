# -*- coding: utf-8 -*-

"""Migrate the Archivematica agent version string to Archivematica-1.9."""
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration_down(apps, _):
    """Undo the migration if requested."""
    agent = apps.get_model("main", "Agent")
    agent.objects.filter(
        identifiertype="preservation system", name="Archivematica"
    ).update(identifiervalue="Archivematica-1.9")


def data_migration_up(apps, _):
    """Update the application agent version in the database."""
    agent = apps.get_model("main", "Agent")
    agent.objects.filter(
        identifiertype="preservation system", name="Archivematica"
    ).update(identifiervalue="Archivematica-1.10")


class Migration(migrations.Migration):
    """Run the migration to update the Archivematica agent version string."""

    dependencies = [("main", "0067_delete_workflow_models")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
