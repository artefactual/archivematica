# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import migrations


def data_migration_up(apps, schema_editor):
    """Update identification tools FIDO and Siegfried to current
    versions, allowing for integration of PRONOM 96.
    """
    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Update Fido tool
    idtool.objects.filter(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44").update(
        version="1.4.1", slug="fido-141"
    )

    # Create new command using the new version of Fido
    old_fido_command = idcommand.objects.get(
        uuid="e586f750-6230-42d7-8d12-1e24ca2aa658"
    )

    # Create new FIDO, but do not enable
    idcommand.objects.create(
        replaces_id="e586f750-6230-42d7-8d12-1e24ca2aa658",
        uuid="ff2c0b52-741d-4f7a-9b52-ba3529051af3",
        description="Identify using Fido 1.4.1",
        config=old_fido_command.config,
        script=old_fido_command.script,
        script_type=old_fido_command.script_type,
        tool=idtool.objects.get(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44"),
        enabled=False,
    )

    # Update Siegfried tool
    old_siegfried_command = idcommand.objects.get(
        uuid="df074736-e2f7-4102-b25d-569c099d410c"
    )

    idtool.objects.filter(uuid="454df69d-5cc0-49fc-93e4-6fbb6ac659e7").update(
        version="1.8.0", slug="siegfried-180"
    )

    # Create new command using the new version of Siegfried
    idcommand.objects.create(
        replaces_id="df074736-e2f7-4102-b25d-569c099d410c",
        uuid="9402ad69-f045-4d0a-8042-9c990645910a",
        description="Identify using Siegfried 1.8.0",
        config=old_siegfried_command.config,
        script=old_siegfried_command.script,
        script_type=old_siegfried_command.script_type,
        tool=idtool.objects.get(uuid="454df69d-5cc0-49fc-93e4-6fbb6ac659e7"),
        enabled=True,
    )


def data_migration_down(apps, schema_editor):
    """Revert FIDO and Siegfriend to previous versions
    """
    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Remove new ID Commands
    idcommand.objects.filter(uuid="ff2c0b52-741d-4f7a-9b52-ba3529051af3").delete()
    idcommand.objects.filter(uuid="9402ad69-f045-4d0a-8042-9c990645910a").delete()

    # Revert Fido tool
    idtool.objects.filter(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44").update(
        version="1.3.12", slug="fido-1312"
    )

    # Revert Siegfried tool
    idtool.objects.filter(uuid="454df69d-5cc0-49fc-93e4-6fbb6ac659e7").update(
        version="1.7.6", slug="siegfried-176"
    )

    # Restore Fido command
    idcommand.objects.filter(uuid="e586f750-6230-42d7-8d12-1e24ca2aa658").update(
        enabled=True
    )

    # Restore Siegfried command
    idcommand.objects.filter(uuid="df074736-e2f7-4102-b25d-569c099d410c").update(
        enabled=True
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0032_pronom_96")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
