from __future__ import unicode_literals

from django.db import migrations

import main.processWorkflowJson as workflow

# Json links definitions to read in.
JSON_LINKS = "/src/dashboard/src/main/workflows/dataverse_foreign_keys.json"


# Primary entry point for the data migration.
def data_migration_up(apps, schema_editor):
    workflow.read_workflow(apps, schema_editor, JSON_LINKS)


class Migration(migrations.Migration):
    dependencies = [("main", "0054_dataverse_transfer_type")]
    operations = [migrations.RunPython(data_migration_up)]
