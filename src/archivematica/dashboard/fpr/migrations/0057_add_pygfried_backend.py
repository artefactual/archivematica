from django.apps.registry import Apps
from django.db import migrations
from django.db import models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

PYGFRIED_TOOL_UUID = "851bcb6d-0304-43b7-931f-774175ac6987"
PYGFRIED_TOOL_SLUG = "pygfried-0170"
PYGFRIED_COMMAND_UUID = "de2759e9-31e1-48d6-810d-41b0cb77c27c"
SIEGFRIED_COMMAND_UUID = "4d3cacf4-e298-47cd-a1e4-460093f1c99a"


def data_migration_up(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Create the Pygfried tool and its disabled identification command."""

    IDTool = apps.get_model("fpr", "IDTool")
    IDCommand = apps.get_model("fpr", "IDCommand")

    tool = IDTool.objects.filter(uuid=PYGFRIED_TOOL_UUID).first()
    if tool is None:
        tool = IDTool.objects.filter(slug=PYGFRIED_TOOL_SLUG).first()
    if tool is None:
        tool = IDTool(
            uuid=PYGFRIED_TOOL_UUID,
            description="Pygfried",
            version="0.17.0",
            slug=PYGFRIED_TOOL_SLUG,
            enabled=True,
        )
        # The historical model does not include IDTool._slug(), which its
        # AutoSlugField references. A raw save preserves the explicit slug.
        tool.save_base(raw=True, using=schema_editor.connection.alias)

    IDCommand.objects.get_or_create(
        uuid=PYGFRIED_COMMAND_UUID,
        defaults={
            "description": "Identify using Pygfried 0.17.0",
            "config": "PUID",
            "script": "",
            "script_type": "pygfried",
            "tool": tool,
            "enabled": False,
        },
    )


def data_migration_down(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Remove Pygfried and reactivate Siegfried if necessary."""

    IDTool = apps.get_model("fpr", "IDTool")
    IDCommand = apps.get_model("fpr", "IDCommand")

    command = IDCommand.objects.filter(uuid=PYGFRIED_COMMAND_UUID).first()
    restore_siegfried = command is not None and command.enabled
    if command is not None:
        command.delete()
    IDTool.objects.filter(uuid=PYGFRIED_TOOL_UUID).delete()
    if restore_siegfried:
        IDCommand.objects.filter(uuid=SIEGFRIED_COMMAND_UUID).update(enabled=True)


class Migration(migrations.Migration):
    dependencies = [("fpr", "0056_add_batch_idcommands")]
    operations = [
        migrations.AlterField(
            model_name="idcommand",
            name="script_type",
            field=models.CharField(
                choices=[
                    ("bashScript", "Bash script"),
                    ("pythonScript", "Python script"),
                    ("command", "Command line"),
                    ("as_is", "No shebang needed"),
                    ("fido", "Fido CLI"),
                    ("siegfried", "Siegfried CLI"),
                    ("pygfried", "Pygfried"),
                ],
                max_length=16,
                verbose_name="execution mode",
            ),
        ),
        migrations.RunPython(data_migration_up, data_migration_down),
    ]
