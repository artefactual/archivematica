# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    IDTool = apps.get_model("fpr", "IDTool")
    IDTool.objects.filter(description="Fido", version="1.3.4").update(version="1.3.5")
    IDTool.objects.filter(description="Siegfried", version="1.5.0").update(
        version="1.6.7"
    )


def reverse_migration(apps, schema_editor):
    IDTool = apps.get_model("fpr", "IDTool")
    IDTool.objects.filter(description="Fido", version="1.3.5").update(version="1.3.4")
    IDTool.objects.filter(description="Siegfried", version="1.6.7").update(
        version="1.5.0"
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0004_pronom_88")]

    operations = [migrations.RunPython(data_migration, reverse_migration)]
