# -*- coding: utf-8 -*-
"""Migration to create a new Dataverse set of chain-links inside Archivematica.
"""
from __future__ import unicode_literals

from django.db import migrations

import main.processWorkflowJson as workflow


# Json links definitions to read in.
JSON_LINKS = "/src/dashboard/src/main/workflows/dataverse_primary_workflow.json"


# Primary entry point for the data migration.
def data_migration_up(apps, schema_editor):
    workflow.read_workflow(apps, schema_editor, JSON_LINKS)


class Migration(migrations.Migration):
    dependencies = [("main", "0055_dataverse_foreign_keys")]
    operations = [migrations.RunPython(data_migration_up)]
