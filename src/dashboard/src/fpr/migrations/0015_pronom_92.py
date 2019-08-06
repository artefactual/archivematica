# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

from django.core.management import call_command
from django.db import migrations


def data_migration(apps, schema_editor):
    fixture_file = os.path.join(os.path.dirname(__file__), "pronom_92.json")
    call_command("loaddata", fixture_file, app_label="fpr")

    Format = apps.get_model("fpr", "Format")
    FormatVersion = apps.get_model("fpr", "FormatVersion")

    Format.objects.filter(uuid="9b3f9406-a375-4b66-9081-61a317e68cbf").update(
        group_id="fdf9e267-a18c-46a4-a162-b81bcba6322f"
    )

    Format.objects.filter(uuid="d4bfbd9b-15fc-4992-98cb-7cea13879307").update(
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e"
    )

    Format.objects.filter(uuid="204309aa-fd1a-47a3-9759-cc5dd5e5a5cc").update(
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e"
    )

    Format.objects.filter(uuid="51cc4e02-c7ef-404e-b8e7-025f60f3efea").update(
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e"
    )

    Format.objects.filter(uuid="082c3b92-4940-4b77-8df2-d04be20f3a9b").update(
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e"
    )

    Format.objects.filter(uuid="996b0720-d6a5-47b5-acaa-3acab09e0a5c").update(
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e"
    )

    Format.objects.filter(uuid="651911e6-0ff3-40a4-ad37-ec5149367c6e").update(
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e"
    )

    Format.objects.filter(uuid="20e28493-e0d2-4413-b431-6626f14c3763").update(
        group_id="57361413-1c3b-405d-a9c0-7d3ea381090e"
    )

    FormatVersion.objects.filter(uuid="e2534186-ed8d-4da1-9639-2a80028a2469").update(
        enabled=False
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0014_fix_fits_command")]

    operations = [migrations.RunPython(data_migration)]
