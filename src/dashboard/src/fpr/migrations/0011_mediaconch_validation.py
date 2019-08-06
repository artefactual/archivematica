# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os

from django.db import migrations


HERE = os.path.dirname(os.path.abspath(__file__))
MIGR_DATA = os.path.join(os.path.dirname(HERE), "migrations-data")
VALIDATE_CMD_FNM = os.path.join(MIGR_DATA, "mc_validate_cmd.py")


def data_migration(apps, schema_editor):
    """Create an FPR tool, command, and rule for MediaConch file validation
    (i.e., .mkv implementation checks)

    Creates the following:

    - MediaConch FPTool
    - MediaConch FPCommand for validation (using
        migrations-data/mc_validate_cmd.py)
    - MediaConch FPRule for validation of .mkv using above command
    """

    FPTool = apps.get_model("fpr", "FPTool")
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")
    FormatVersion = apps.get_model("fpr", "FormatVersion")
    mkv_format = FormatVersion.objects.get(description="Generic MKV")

    # MediaConch FPR Tool
    mediaconch_tool_uuid = "f79c56f1-2d42-440a-8a1f-f40888e24bca"
    mediaconch_tool = FPTool.objects.create(
        uuid=mediaconch_tool_uuid,
        description="MediaConch",
        version="18.03",
        enabled=True,
        slug="mediaconch-1803",
    )

    # MediaConch Validation FPR Command
    with open(VALIDATE_CMD_FNM) as filei:
        mediaconch_command_script = filei.read()
    mediaconch_command_uuid = "287656fb-e58f-4967-bf72-0bae3bbb5ca8"
    mediaconch_command = FPCommand.objects.create(
        uuid=mediaconch_command_uuid,
        tool=mediaconch_tool,
        description="Validate using MediaConch",
        command=mediaconch_command_script,
        script_type="pythonScript",
        command_usage="validation",
    )

    # MediaConch-against-MKV-for-validation FPR Rule.
    mediaconch_mkv_rule_uuid = "a2fb0477-6cde-43f8-a1c9-49834913d588"
    FPRule.objects.create(
        uuid=mediaconch_mkv_rule_uuid,
        purpose="validation",
        command=mediaconch_command,
        format=mkv_format,
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0010_update_fido_136")]

    operations = [migrations.RunPython(data_migration)]
