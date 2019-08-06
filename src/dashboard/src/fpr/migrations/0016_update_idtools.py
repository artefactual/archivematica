# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    IDTool = apps.get_model("fpr", "IDTool")
    IDCommand = apps.get_model("fpr", "IDCommand")

    # Update Fido tool
    tool = IDTool.objects.get(uuid="c33c9d4d-121f-4db1-aa31-3d248c705e44")
    tool.version = "1.3.7"
    tool._slug = "fido-137"
    tool.save()

    # Create new command using the new version of Fido
    old_command = IDCommand.objects.get(
        uuid="a8e45bc1-eb35-4545-885c-dd552f1fde9a", enabled=True
    )
    IDCommand.objects.create(
        uuid="76006ad7-a401-48f6-98f6-2efc01003276",
        description="Identify using Fido",
        config=old_command.config,
        script=old_command.script,
        script_type=old_command.script_type,
        tool=tool,
        enabled=True,
    )
    old_command.enabled = False
    old_command.save()

    # Update Siegfried tool
    tool = IDTool.objects.get(uuid="454df69d-5cc0-49fc-93e4-6fbb6ac659e7")
    tool.version = "1.7.6"
    tool._slug = "siegfried-176"
    tool.save()

    # Create new command using the new version of Siegfried
    old_command = IDCommand.objects.get(
        uuid="9d2cefc1-2bd2-44e4-8d55-6cf8151eecff", enabled=True
    )
    IDCommand.objects.create(
        uuid="df074736-e2f7-4102-b25d-569c099d410c",
        description=old_command.description,
        config=old_command.config,
        script=old_command.script,
        script_type=old_command.script_type,
        tool=tool,
        enabled=True,
    )
    old_command.enabled = False
    old_command.save()


class Migration(migrations.Migration):

    dependencies = [("fpr", "0015_pronom_92")]

    operations = [migrations.RunPython(data_migration)]
