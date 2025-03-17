from django.db import migrations

OLD_FIDO_CMD_DESCRIPTION = "Identify using Fido 1.4.1"
OLD_FIDO_CMD_UUID = "8383e9eb-0d3c-4872-ae63-05405a156502"
OLD_FIDO_TOOL_SLUG = "fido-141"
OLD_FIDO_TOOL_UUID = "c33c9d4d-121f-4db1-aa31-3d248c705e44"
OLD_FIDO_TOOL_VERSION = "1.4.1"

OLD_SIEGFRIED_CMD_DESCRIPTION = "Identify using Siegfried 1.8.0"
OLD_SIEGFRIED_CMD_UUID = "e24cf2d5-51ac-4bed-9ff6-cb691d895ade"
OLD_SIEGFRIED_TOOL_SLUG = "siegfried-180"
OLD_SIEGFRIED_TOOL_UUID = "454df69d-5cc0-49fc-93e4-6fbb6ac659e7"
OLD_SIEGFRIED_TOOL_VERSION = "1.8.0"

NEW_FIDO_CMD_DESCRIPTION = "Identify using Fido 1.6.1"
NEW_FIDO_CMD_UUID = "49bc44de-86cf-4e53-9ae1-137f08a5a93c"
NEW_FIDO_TOOL_SLUG = "fido-161"
NEW_FIDO_TOOL_VERSION = "1.6.1"

NEW_SIEGFRIED_CMD_DESCRIPTION = "Identify using Siegfried 1.9.6"
NEW_SIEGFRIED_CMD_UUID = "5dfe5362-3ed4-4ff5-9c91-81d1a24a796b"
NEW_SIEGFRIED_TOOL_SLUG = "siegfried-196"
NEW_SIEGFRIED_TOOL_VERSION = "1.9.6"


def data_migration_up(apps, schema_editor):
    """Update identification tools FIDO and Siegfried to current
    versions, allowing for integration of PRONOM 109.
    """
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
    """Revert FIDO and Siegfriend to previous versions"""
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
    dependencies = [("fpr", "0036_pronom_109")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
