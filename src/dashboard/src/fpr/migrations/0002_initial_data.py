# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

from django.core.management import call_command
from django.db import migrations


def load_fixtures(apps, schema_editor):
    fixture_file = os.path.join(os.path.dirname(__file__), "initial_data.json")
    call_command("loaddata", fixture_file, app_label="main")


class Migration(migrations.Migration):

    dependencies = [("fpr", "0001_initial")]

    operations = [migrations.RunPython(load_fixtures)]
