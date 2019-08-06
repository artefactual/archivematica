# -*- coding: utf-8 -*-
"""Stop using sudo in the `Transcoding to plain svg with inkscape` command."""
from __future__ import absolute_import, unicode_literals

from django.db import migrations


INKSCAPE_TOOL_UUID = "34afccc3-2cfd-4780-ba56-06221f1bfe18"

# Normalization rules using `Transcoding to plain svg with inkscape`.
INKSCAPE_SVG_RULES = (
    "363f452e-a41b-46f3-865b-80a249493dfd",
    "9591f5e1-7274-4f25-a70a-5d58c67a9896",
    "3e9ad70d-67db-489e-a64d-b52997e267fb",
    "a60bc8f5-4fe9-4e9f-b1e2-a1a1923cad56",
    "8d3572d1-dbf4-4cbd-ace6-78d0130d109d",
    "815413a5-e3f1-4f5b-80cf-affe712227ad",
    "32b1a6c3-ed35-44ea-9902-5c8b1cba99ca",
    "dfb57e0b-8547-4d49-bd09-c80dd6a26e5a",
)

OLD_INKSCAPE_CMD_UUID = "64c450b4-135c-46d1-a9aa-3f9b15671677"
NEW_INKSCAPE_CMD_UUID = "cf8b44c8-ba16-44cd-8b47-cb29d52fbac4"


def data_migration_up(apps, schema_editor):
    """Update command to stop using sudo."""
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    # The only difference with the new command is that it's not using sudo.
    new_cmd = (
        '/usr/bin/inkscape "%fileFullName%" --export-plain-svg="%outputDirectory%%prefix%%fileName%%postfix%.svg"'
        '\nchmod 777 "%outputDirectory%%prefix%%fileName%%postfix%.svg"'
    )

    # Replace the existing command with the following.
    FPCommand.objects.create(
        uuid=NEW_INKSCAPE_CMD_UUID,
        replaces_id=OLD_INKSCAPE_CMD_UUID,
        tool_id=INKSCAPE_TOOL_UUID,
        event_detail_command_id="1db2deea-01dd-43e5-9f27-dc9ed02acdfe",
        verification_command_id="a9111dc0-edc9-47f8-85e5-ad4013971361",
        output_format_id="8ba2101d-3f3c-4620-a0fa-a75cf5f5ec27",
        enabled=True,
        command=new_cmd,
        script_type="bashScript",
        command_usage="normalization",
        output_location="%outputDirectory%%prefix%%fileName%%postfix%.svg",
        description="Transcoding to plain svg with inkscape",
    )

    # Update existing rules.
    FPRule.objects.filter(uuid__in=INKSCAPE_SVG_RULES).update(
        command_id=NEW_INKSCAPE_CMD_UUID
    )


def data_migration_down(apps, schema_editor):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    # The order matters. We make sure that the rules point to the previous
    # command before the latter is deleted. Otherwise our rules would be
    # deleted by Django's on cascade mechanism.
    FPRule.objects.filter(uuid__in=INKSCAPE_SVG_RULES).update(
        command_id=OLD_INKSCAPE_CMD_UUID
    )

    FPCommand.objects.filter(uuid=NEW_INKSCAPE_CMD_UUID).delete()


class Migration(migrations.Migration):

    dependencies = [("fpr", "0028_idcommand_unique_enabled")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
