from django.db import migrations
from django.db.models import Q


def remove_maildir_commands(apps):
    FPCommand = apps.get_model("fpr", "FPCommand")

    # Deleting the normalization command deletes the related rules as well.
    normalization_command = Q(
        description="Transcoding maildir to mbox",
        command_usage="normalization",
    )
    event_detail_command = Q(
        description="Transcoding maildir to mbox event detail",
        command_usage="event_detail",
    )

    FPCommand.objects.filter(normalization_command | event_detail_command).delete()


def data_migration_up(apps, schema_editor):
    remove_maildir_commands(apps)


class Migration(migrations.Migration):
    dependencies = [("fpr", "0050_remove_usr_dir_references")]

    operations = [migrations.RunPython(data_migration_up, migrations.RunPython.noop)]
