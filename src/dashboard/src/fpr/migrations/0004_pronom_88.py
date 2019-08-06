# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

from django.core.management import call_command
from django.db import migrations


def load_fixtures(apps, schema_editor):
    fixture_file = os.path.join(os.path.dirname(__file__), "pronom_88.json")
    call_command("loaddata", fixture_file, app_label="fpr")


class Migration(migrations.Migration):

    dependencies = [("fpr", "0003_pronom_84")]

    operations = [migrations.RunPython(load_fixtures)]
