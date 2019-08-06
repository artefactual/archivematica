# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    MicroServiceChoiceReplacementDic = apps.get_model(
        "main", "MicroServiceChoiceReplacementDic"
    )

    MicroServiceChoiceReplacementDic.objects.filter(
        replacementdic='{"%IDCommand%":"41efbe1b-3fc7-4b24-9290-d0fb5d0ea9e9"}'
    ).update(description="Identify by File Extension")
    MicroServiceChoiceReplacementDic.objects.filter(
        replacementdic='{"%IDCommand%":"a8e45bc1-eb35-4545-885c-dd552f1fde9a"}'
    ).update(description="Identify using Fido")
    MicroServiceChoiceReplacementDic.objects.filter(
        replacementdic='{"%IDCommand%":"8cc792b4-362d-4002-8981-a4e808c04b24"}'
    ).update(description="Identify using Siegfried")


class Migration(migrations.Migration):

    dependencies = [("main", "0011_version_number")]

    operations = [migrations.RunPython(data_migration)]
