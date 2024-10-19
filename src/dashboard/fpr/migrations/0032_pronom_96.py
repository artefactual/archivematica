import os

from django.core.management import call_command
from django.db import migrations


def data_migration(apps, schema_editor):
    fixture_file = os.path.join(os.path.dirname(__file__), "pronom_96.json")
    call_command("loaddata", fixture_file, app_label="fpr")


class Migration(migrations.Migration):
    dependencies = [("fpr", "0031_update_normalization_rules")]

    operations = [migrations.RunPython(data_migration)]
