from django.apps.registry import Apps
from django.db import migrations
from django.db import models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

OLD_FIDO_COMMAND_UUID = "c5fa04a8-aae6-430e-bec6-8922341348ab"
NEW_FIDO_COMMAND_UUID = "595853b2-b4b4-4d30-b989-e1109732ed1c"

OLD_SIEGFRIED_COMMAND_UUID = "3634f5e1-65ba-423f-82c2-c0ec34560e9d"
NEW_SIEGFRIED_COMMAND_UUID = "4d3cacf4-e298-47cd-a1e4-460093f1c99a"


def _replace_command(
    IDCommand,
    *,
    old_uuid: str,
    new_uuid: str,
    description: str,
    script_type: str,
) -> None:
    """Create a batch command that supersedes an existing command."""

    old_command = IDCommand.objects.filter(uuid=old_uuid).first()
    if old_command is None:
        return

    enabled = old_command.enabled
    old_command.enabled = False
    old_command.save(update_fields=["enabled"])
    IDCommand.objects.create(
        replaces=old_command,
        uuid=new_uuid,
        description=description,
        config=old_command.config,
        script="",
        script_type=script_type,
        tool=old_command.tool,
        enabled=enabled,
    )


def data_migration_up(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Replace standard Fido and Siegfried commands with batch variants."""

    IDCommand = apps.get_model("fpr", "IDCommand")

    _replace_command(
        IDCommand,
        old_uuid=OLD_FIDO_COMMAND_UUID,
        new_uuid=NEW_FIDO_COMMAND_UUID,
        description="Identify using Fido 1.6.4rc1 in batch mode",
        script_type="fido",
    )
    _replace_command(
        IDCommand,
        old_uuid=OLD_SIEGFRIED_COMMAND_UUID,
        new_uuid=NEW_SIEGFRIED_COMMAND_UUID,
        description="Identify using Siegfried 1.11.5 in batch mode",
        script_type="siegfried",
    )


def _restore_command(IDCommand, *, old_uuid: str, new_uuid: str) -> None:
    """Delete a batch command and restore its predecessor's state."""

    new_command = IDCommand.objects.filter(uuid=new_uuid).first()
    if new_command is None:
        return

    enabled = new_command.enabled
    new_command.delete()
    IDCommand.objects.filter(uuid=old_uuid).update(enabled=enabled)


def data_migration_down(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Restore the standard non-batch Fido and Siegfried commands."""

    IDCommand = apps.get_model("fpr", "IDCommand")

    _restore_command(
        IDCommand,
        old_uuid=OLD_FIDO_COMMAND_UUID,
        new_uuid=NEW_FIDO_COMMAND_UUID,
    )
    _restore_command(
        IDCommand,
        old_uuid=OLD_SIEGFRIED_COMMAND_UUID,
        new_uuid=NEW_SIEGFRIED_COMMAND_UUID,
    )


class Migration(migrations.Migration):
    dependencies = [("fpr", "0055_update_idtools")]
    operations = [
        migrations.AlterField(
            model_name="idcommand",
            name="script",
            field=models.TextField(
                blank=True,
                help_text="Script to be executed by script-based commands.",
                verbose_name="script",
            ),
        ),
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
                ],
                max_length=16,
                verbose_name="execution mode",
            ),
        ),
        migrations.RunPython(data_migration_up, data_migration_down),
    ]
