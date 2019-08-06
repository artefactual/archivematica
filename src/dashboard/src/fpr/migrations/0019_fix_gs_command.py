# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Fix the Ghostscript normalization command "Command Transcoding to pdfa
    with Ghostscript" so that it documents its true output format as PDF/A 1b
    (fmt/354) and not PDF/A 1a (fmt/95).
    """
    FPCommand = apps.get_model("fpr", "FPCommand")
    FormatVersion = apps.get_model("fpr", "FormatVersion")
    true_format_version = FormatVersion.objects.get(pronom_id="fmt/354")
    FPCommand.objects.filter(uuid="d6a33093-85d5-4088-83e1-b7a774a826bd").update(
        output_format=true_format_version
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0018_slug_unique")]

    operations = [migrations.RunPython(data_migration)]
