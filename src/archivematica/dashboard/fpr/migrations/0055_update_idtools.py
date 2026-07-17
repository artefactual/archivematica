from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

OLD_FIDO_CMD_UUID = "4ab42bc8-1537-4fa9-9c54-e454f2c5dcb7"
OLD_FIDO_TOOL_SLUG = "fido-163rc1"
OLD_FIDO_TOOL_UUID = "c33c9d4d-121f-4db1-aa31-3d248c705e44"
OLD_FIDO_TOOL_VERSION = "1.6.3rc1"

OLD_SIEGFRIED_CMD_UUID = "4914841c-3555-4519-86e3-5bf622d28351"
OLD_SIEGFRIED_TOOL_SLUG = "siegfried-1112"
OLD_SIEGFRIED_TOOL_UUID = "454df69d-5cc0-49fc-93e4-6fbb6ac659e7"
OLD_SIEGFRIED_TOOL_VERSION = "1.11.2"

NEW_FIDO_CMD_DESCRIPTION = "Identify using Fido 1.6.4rc1"
NEW_FIDO_CMD_UUID = "c5fa04a8-aae6-430e-bec6-8922341348ab"
NEW_FIDO_TOOL_SLUG = "fido-164rc1"
NEW_FIDO_TOOL_VERSION = "1.6.4rc1"

NEW_SIEGFRIED_CMD_DESCRIPTION = "Identify using Siegfried 1.11.5"
NEW_SIEGFRIED_CMD_UUID = "3634f5e1-65ba-423f-82c2-c0ec34560e9d"
NEW_SIEGFRIED_TOOL_SLUG = "siegfried-1115"
NEW_SIEGFRIED_TOOL_VERSION = "1.11.5"


def data_migration_up(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Update Fido tool.
    idtool.objects.filter(uuid=OLD_FIDO_TOOL_UUID).update(
        version=NEW_FIDO_TOOL_VERSION, slug=NEW_FIDO_TOOL_SLUG
    )

    # Create a new Fido command, but do not enable it.
    old_fido_command = idcommand.objects.get(uuid=OLD_FIDO_CMD_UUID)
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

    # Replace the enabled Siegfried command with the new version.
    old_siegfried_command = idcommand.objects.get(uuid=OLD_SIEGFRIED_CMD_UUID)
    old_siegfried_command.enabled = False
    old_siegfried_command.save()
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


def data_migration_down(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    idcommand.objects.filter(uuid=NEW_FIDO_CMD_UUID).delete()
    idcommand.objects.filter(uuid=NEW_SIEGFRIED_CMD_UUID).delete()

    idtool.objects.filter(uuid=OLD_FIDO_TOOL_UUID).update(
        version=OLD_FIDO_TOOL_VERSION, slug=OLD_FIDO_TOOL_SLUG
    )
    idtool.objects.filter(uuid=OLD_SIEGFRIED_TOOL_UUID).update(
        version=OLD_SIEGFRIED_TOOL_VERSION, slug=OLD_SIEGFRIED_TOOL_SLUG
    )
    idcommand.objects.filter(uuid=OLD_SIEGFRIED_CMD_UUID).update(enabled=True)


class Migration(migrations.Migration):
    dependencies = [("fpr", "0054_pronom_124")]
    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
