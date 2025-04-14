import pathlib

from django.core.management import call_command
from django.db import migrations


def data_migration_up(apps, schema_editor):
    fixture_file = pathlib.Path(__file__).parent / "pronom_120.json"
    call_command("loaddata", fixture_file, app_label="fpr")


class Migration(migrations.Migration):
    dependencies = [("fpr", "0047_update_format_groups")]
    operations = [migrations.RunPython(data_migration_up, migrations.RunPython.noop)]
