from django.db import migrations


def data_migration(apps, schema_editor):
    FPTool = apps.get_model("fpr", "FPTool")
    FPTool.objects.filter(description="FITS").delete()


class Migration(migrations.Migration):
    dependencies = [("fpr", "0043_update_default_thumbnail_command")]

    operations = [migrations.RunPython(data_migration, migrations.RunPython.noop)]
