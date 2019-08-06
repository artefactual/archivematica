# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration_up(apps, schema_editor):
    """
    Update identification tool FIDO to 1.3.12, correcting a
    character-spacing issue bug identified in PRONOM94 (again)
    """

    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Update Fido tool
    idtool.objects.filter(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44").update(
        version="1.3.12", slug="fido-1312"
    )

    # Create new command using the new version of Fido
    old_fido_command = idcommand.objects.get(
        uuid="e586f750-6230-42d7-8d12-1e24ca2aa658"
    )

    idcommand.objects.create(
        uuid="213d1589-c255-474f-81ac-f0a618181e40",
        description="Identify using Fido 1.3.12",
        config=old_fido_command.config,
        script=old_fido_command.script,
        script_type=old_fido_command.script_type,
        tool=idtool.objects.get(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44"),
        enabled=True,
    )
    old_fido_command.enabled = False
    old_fido_command.save()


def data_migration_down(apps, schema_editor):
    """
    Revert FIDO to previous version
    """

    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Remove new ID Commands
    idcommand.objects.filter(uuid="213d1589-c255-474f-81ac-f0a618181e40").delete()

    # Revert Fido tool
    idtool.objects.filter(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44").update(
        version="1.3.10", slug="fido-1310"
    )

    # Restore Fido command
    idcommand.objects.filter(uuid="e586f750-6230-42d7-8d12-1e24ca2aa658").update(
        enabled=True
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0024_update_fido")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
