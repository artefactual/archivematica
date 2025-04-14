from django.db import migrations

OLD_FIDO_CMD_DESCRIPTION = "Identify using Fido 1.6.2rc1"
OLD_FIDO_CMD_UUID = "2cc8bb8e-1f6f-42f1-90b6-31207612c4c9"
OLD_FIDO_TOOL_SLUG = "fido-162rc1"
OLD_FIDO_TOOL_UUID = "c33c9d4d-121f-4db1-aa31-3d248c705e44"
OLD_FIDO_TOOL_VERSION = "1.6.2rc1"

OLD_SIEGFRIED_CMD_DESCRIPTION = "Identify using Siegfried 1.11.0"
OLD_SIEGFRIED_CMD_UUID = "88c747f5-7b6c-4913-8dc2-3957dcd5e6b8"
OLD_SIEGFRIED_TOOL_SLUG = "siegfried-1110"
OLD_SIEGFRIED_TOOL_UUID = "454df69d-5cc0-49fc-93e4-6fbb6ac659e7"
OLD_SIEGFRIED_TOOL_VERSION = "1.11.0"

NEW_FIDO_CMD_DESCRIPTION = "Identify using Fido 1.6.3rc1"
NEW_FIDO_CMD_UUID = "4ab42bc8-1537-4fa9-9c54-e454f2c5dcb7"
NEW_FIDO_TOOL_SLUG = "fido-163rc1"
NEW_FIDO_TOOL_VERSION = "1.6.3rc1"

NEW_SIEGFRIED_CMD_DESCRIPTION = "Identify using Siegfried 1.11.2"
NEW_SIEGFRIED_CMD_UUID = "4914841c-3555-4519-86e3-5bf622d28351"
NEW_SIEGFRIED_TOOL_SLUG = "siegfried-1112"
NEW_SIEGFRIED_TOOL_VERSION = "1.11.2"


def data_migration_up(apps, schema_editor):
    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Update FIDO tool
    idtool.objects.filter(uuid=OLD_FIDO_TOOL_UUID).update(
        version=NEW_FIDO_TOOL_VERSION, slug=NEW_FIDO_TOOL_SLUG
    )

    # Find old FIDO command.
    old_fido_command = idcommand.objects.get(uuid=OLD_FIDO_CMD_UUID)

    # Create new FIDO, but do not enable.
    idcommand.objects.create(
        replaces=old_fido_command,
        uuid=NEW_FIDO_CMD_UUID,
        description=NEW_FIDO_CMD_DESCRIPTION,
        config=old_fido_command.config,
        script=old_fido_command.script,
        script_type=old_fido_command.script_type,
        tool=idtool.objects.get(uuid=OLD_FIDO_TOOL_UUID),
        enabled=False,
    )

    # Update Siegfried tool.
    idtool.objects.filter(uuid=OLD_SIEGFRIED_TOOL_UUID).update(
        version=NEW_SIEGFRIED_TOOL_VERSION, slug=NEW_SIEGFRIED_TOOL_SLUG
    )

    # Find old Siegfried command and disable it.
    old_siegfried_command = idcommand.objects.get(uuid=OLD_SIEGFRIED_CMD_UUID)
    old_siegfried_command.enabled = False
    old_siegfried_command.save()

    # Create new command using the new version of Siegfried
    idcommand.objects.create(
        replaces=old_siegfried_command,
        uuid=NEW_SIEGFRIED_CMD_UUID,
        description=NEW_SIEGFRIED_CMD_DESCRIPTION,
        config=old_siegfried_command.config,
        script=old_siegfried_command.script,
        script_type=old_siegfried_command.script_type,
        tool=idtool.objects.get(uuid=OLD_SIEGFRIED_TOOL_UUID),
        enabled=True,
    )


def data_migration_down(apps, schema_editor):
    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Remove new ID Commands
    idcommand.objects.filter(uuid=NEW_FIDO_CMD_UUID).delete()
    idcommand.objects.filter(uuid=NEW_SIEGFRIED_CMD_UUID).delete()

    # Revert Fido tool
    idtool.objects.filter(uuid=OLD_FIDO_TOOL_UUID).update(
        version=OLD_FIDO_TOOL_VERSION, slug=OLD_FIDO_TOOL_SLUG
    )

    # Revert Siegfried tool
    idtool.objects.filter(uuid=OLD_SIEGFRIED_TOOL_UUID).update(
        version=OLD_SIEGFRIED_TOOL_VERSION, slug=OLD_SIEGFRIED_TOOL_SLUG
    )

    # Restore old Siegfried command.
    idcommand.objects.filter(uuid=OLD_SIEGFRIED_CMD_UUID).update(enabled=True)


class Migration(migrations.Migration):
    dependencies = [("fpr", "0048_pronom_120")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
