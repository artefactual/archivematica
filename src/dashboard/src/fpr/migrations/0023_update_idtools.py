# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration_up(apps, schema_editor):
    """Update identification tools FIDO and Siegfried to current
    versions, allowing for integration of PRONOM 94.
    """
    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Update Fido tool
    idtool.objects.filter(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44").update(
        version="1.3.9", slug="fido-139"
    )

    # Create new command using the new version of Fido
    old_fido_command = idcommand.objects.get(
        uuid="76006ad7-a401-48f6-98f6-2efc01003276"
    )

    idcommand.objects.create(
        uuid="6fa7b8d8-10f1-439d-888a-5ccb3a5be492",
        description="Identify using Fido 1.3.9",
        config=old_fido_command.config,
        script=old_fido_command.script,
        script_type=old_fido_command.script_type,
        tool=idtool.objects.get(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44"),
        enabled=True,
    )
    old_fido_command.enabled = False
    old_fido_command.save()

    # Update Siegfried tool
    old_siegfried_command = idcommand.objects.get(
        uuid="df074736-e2f7-4102-b25d-569c099d410c"
    )

    idtool.objects.filter(uuid="454df69d-5cc0-49fc-93e4-6fbb6ac659e7").update(
        version="1.7.10", slug="siegfried-1710"
    )

    # Create new command using the new version of Siegfried
    idcommand.objects.create(
        uuid="75290b14-2931-455f-bdde-3b4b3f8b7f15",
        description="Identify using Siegfried 1.7.10",
        config=old_siegfried_command.config,
        script=old_siegfried_command.script,
        script_type=old_siegfried_command.script_type,
        tool=idtool.objects.get(uuid="454df69d-5cc0-49fc-93e4-6fbb6ac659e7"),
        enabled=True,
    )
    old_siegfried_command.enabled = False
    old_siegfried_command.save()


def data_migration_down(apps, schema_editor):
    """Revert FIDO and Siegfriend to previous versions"""
    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Remove new ID Commands
    idcommand.objects.filter(uuid="6fa7b8d8-10f1-439d-888a-5ccb3a5be492").delete()
    idcommand.objects.filter(uuid="75290b14-2931-455f-bdde-3b4b3f8b7f15").delete()

    # Revert Fido tool
    idtool.objects.filter(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44").update(
        version="1.3.7", slug="fido-137"
    )

    # Revert Siegfried tool
    idtool.objects.filter(uuid="454df69d-5cc0-49fc-93e4-6fbb6ac659e7").update(
        version="1.7.6", slug="siegfried-176"
    )

    # Restore Fido command
    idcommand.objects.filter(uuid="76006ad7-a401-48f6-98f6-2efc01003276").update(
        enabled=True
    )

    # Restore Siegfried command
    idcommand.objects.filter(uuid="df074736-e2f7-4102-b25d-569c099d410c").update(
        enabled=True
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0022_pronom_94")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
