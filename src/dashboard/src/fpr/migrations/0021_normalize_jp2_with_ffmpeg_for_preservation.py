# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


NEW_FFMPEG_CMD_UUID = "66ba8388-2cd2-44a7-9d30-5d194d47c75b"
OLD_CONVERT_RULE_UUID = "76ece049-6812-402e-b231-8cf1445a04b4"
NEW_FFMPEG_RULE_UUID = "b98667be-2614-410b-9079-41942dbc3b32"


def data_migration_up(apps, schema_editor):
    """Fix jp2 not normalizing for preservation. Disable the old command
    based on ImageMagick and create a new command using ffmpeg. This
    corrects a long-standing issue with ImageMagick not supporting
    the libopenjpeg library in Linux core, but ffmpeg is compiled
    with this support.
    See https://github.com/archivematica/Issues/issues/91 for more.
    """
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    ffmpeg_tool_uuid = "fcc4e6d7-d956-40e9-af92-0e544895eb1f"
    jp2_format_uuid = "734edb99-968d-42fc-9fc6-342b86fcb6e6"

    new_cmd = (
        'ffmpeg -vcodec libopenjpeg -i "%fileFullName%"'
        " -compression_algo raw -pix_fmt rgb24"
        ' "%outputDirectory%%prefix%%fileName%%postfix%.tif"'
    )

    FPCommand.objects.create(
        uuid=NEW_FFMPEG_CMD_UUID,
        tool_id=ffmpeg_tool_uuid,
        command_usage="normalization",
        command=new_cmd,
        script_type="command",
        enabled=True,
        output_location="%outputDirectory%%prefix%%fileName%%postfix%.tif",
        output_format_id="2ebdfa17-2257-49f8-8035-5f304bb46918",
        verification_command_id="a9111dc0-edc9-47f8-85e5-ad4013971361",
        description="Transcoding to tif with ffmpeg",
    )

    FPRule.objects.filter(uuid=OLD_CONVERT_RULE_UUID).update(enabled=False)

    FPRule.objects.create(
        uuid=NEW_FFMPEG_RULE_UUID,
        replaces_id=OLD_CONVERT_RULE_UUID,
        format_id=jp2_format_uuid,
        command_id=NEW_FFMPEG_CMD_UUID,
        purpose="preservation",
    )


def data_migration_down(apps, schema_editor):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    # Remove command "Transcoding to tif with ffmpeg" and the new rule.
    FPCommand.objects.filter(uuid=NEW_FFMPEG_CMD_UUID).delete()
    FPRule.objects.filter(uuid=NEW_FFMPEG_RULE_UUID).delete()

    # Restore old rule.
    FPRule.objects.filter(uuid=OLD_CONVERT_RULE_UUID).update(enabled=True)


class Migration(migrations.Migration):

    dependencies = [("fpr", "0020_pronom_93")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
