import uuid

from django.db import migrations

OLD_COMMAND_ID = uuid.UUID("914fe3e5-fa45-47c6-858d-e11bc71f5b76")
NEW_COMMAND_ID = uuid.UUID("8f177f1c-5eac-45c4-aa6f-2214107d1a7b")

COMMANDS = [
    # Extraction -> Extracting 7Zip compatible format.
    uuid.UUID("b8864e2c-87a0-4aec-a8cf-a747a073be28"),
]


def data_migration_up(apps, schema_editor):
    FPCommand = apps.get_model("fpr", "FPCommand")

    # Get the current command.
    old_command = FPCommand.objects.get(uuid=OLD_COMMAND_ID)

    # Add a new command that replaces the current one with a new bash script.
    new_command = FPCommand.objects.create(
        uuid=NEW_COMMAND_ID,
        replaces=old_command,
        tool=old_command.tool,
        enabled=old_command.enabled,
        command=r"echo program=\"7z\"\; version=\"`7z | awk 'NR==3 && /^p7zip Version/ {print; exit} NR==2 {line2=$0} NR==3 {print line2 $0}'`\"",
        script_type=old_command.script_type,
        command_usage=old_command.command_usage,
        description=old_command.description,
    )

    # Update extraction commands that use the event detail command.
    FPCommand.objects.filter(uuid__in=COMMANDS).update(event_detail_command=new_command)

    # Disable previous command.
    FPCommand.objects.filter(uuid=OLD_COMMAND_ID).update(enabled=False)


def data_migration_down(apps, schema_editor):
    FPCommand = apps.get_model("fpr", "FPCommand")

    # Get previous command.
    old_command = FPCommand.objects.get(uuid=OLD_COMMAND_ID)

    # Update extraction commands that use the event detail command.
    FPCommand.objects.filter(uuid__in=COMMANDS).update(event_detail_command=old_command)

    # Delete the newest command.
    FPCommand.objects.filter(uuid=NEW_COMMAND_ID).delete()

    # Re-enable the previous command.
    old_command.enabled = True
    old_command.save()


class Migration(migrations.Migration):
    dependencies = [("fpr", "0044_remove_fits")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
