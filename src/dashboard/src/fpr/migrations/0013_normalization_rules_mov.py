# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """ Create rules for Apple ProRes. """

    FPRule = apps.get_model("fpr", "FPRule")

    format_apple_prores_id = "9dd2784d-fb57-44de-83b2-5cc54703476b"

    rules = [
        {
            "uuid": "52db06e9-ed12-4ca3-83e6-6e867a171dba",
            "purpose": "preservation",
            # Transcoding to mkv with ffmpeg
            "command": "2d991241-e352-4a77-b104-e7e82fb119c4",
        },
        {
            "uuid": "7a2bfddd-0f1d-4027-8087-cba338d1ce80",
            "purpose": "access",
            # Transcoding to mp4 with ffmpeg
            "command": "bb5a6da2-4b89-4f8c-96e3-ca36c55d3337",
        },
        {
            "uuid": "4aafcf44-4d28-4d56-9df1-50be1fd9dd78",
            "purpose": "characterization",
            # ExifTool
            "command": "99d5f508-7733-4e86-883f-bd6abc3fbac7",
        },
        {
            "uuid": "cb95c93c-6cdf-40eb-a328-eb6811daf8c0",
            "purpose": "characterization",
            # FFprobe
            "command": "80314f3c-5d48-4ad1-a9f2-2c0f7c7b229d",
        },
        {
            "uuid": "885de9a4-7463-4914-b40c-780a232e5442",
            "purpose": "characterization",
            # MediaInfo
            "command": "114c9525-d676-4fac-9962-4672faa924bb",
        },
    ]
    for item in rules:
        FPRule.objects.create(
            uuid=item["uuid"],
            purpose=item["purpose"],
            command_id=item["command"],
            format_id=format_apple_prores_id,
            enabled=True,
        )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0012_mediaconch_policy_checks")]

    operations = [migrations.RunPython(data_migration)]
