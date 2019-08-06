# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

from django.core.management import call_command
from django.db import migrations


def data_migration(apps, schema_editor):
    fixture_file = os.path.join(os.path.dirname(__file__), "pronom_93.json")
    call_command("loaddata", fixture_file, app_label="fpr")


class Migration(migrations.Migration):

    dependencies = [("fpr", "0019_fix_gs_command")]

    operations = [migrations.RunPython(data_migration)]
