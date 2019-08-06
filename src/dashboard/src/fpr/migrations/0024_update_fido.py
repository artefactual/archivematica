# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration_up(apps, schema_editor):
    """
    Update identification tool FIDO to 1.3.10, correcting a
    character-spacing issue bug identified in PRONOM94
    """

    idtool = apps.get_model("fpr", "IDTool")
    idcommand = apps.get_model("fpr", "IDCommand")

    # Update Fido tool
    idtool.objects.filter(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44").update(
        version="1.3.10", slug="fido-1310"
    )

    # Create new command using the new version of Fido
    old_fido_command = idcommand.objects.get(
        uuid="6fa7b8d8-10f1-439d-888a-5ccb3a5be492"
    )

    idcommand.objects.create(
        uuid="e586f750-6230-42d7-8d12-1e24ca2aa658",
        description="Identify using Fido 1.3.10",
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
    idcommand.objects.filter(uuid="e586f750-6230-42d7-8d12-1e24ca2aa658").delete()

    # Revert Fido tool
    idtool.objects.filter(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44").update(
        version="1.3.9", slug="fido-139"
    )

    # Restore Fido command
    idcommand.objects.filter(uuid="6fa7b8d8-10f1-439d-888a-5ccb3a5be492").update(
        enabled=True
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0023_update_idtools")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
