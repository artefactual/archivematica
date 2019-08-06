# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

from django.core.management import call_command
from django.db import migrations


def load_fixtures(apps, schema_editor):
    fixture_file = os.path.join(
        os.path.dirname(__file__), "pronom84_formatgroups_new.json"
    )
    call_command("loaddata", fixture_file, app_label="fpr")

    fixture_file = os.path.join(os.path.dirname(__file__), "pronom84_formats_all.json")
    call_command("loaddata", fixture_file, app_label="fpr")

    fixture_file = os.path.join(
        os.path.dirname(__file__), "pronom84_formatversions_all.json"
    )
    call_command("loaddata", fixture_file, app_label="fpr")

    fixture_file = os.path.join(os.path.dirname(__file__), "pronom84_fptools_all.json")
    call_command("loaddata", fixture_file, app_label="fpr")

    fixture_file = os.path.join(os.path.dirname(__file__), "pronom84_idtools_all.json")
    call_command("loaddata", fixture_file, app_label="fpr")

    fixture_file = os.path.join(
        os.path.dirname(__file__), "pronom84_idcommands_all.json"
    )
    call_command("loaddata", fixture_file, app_label="fpr")

    fixture_file = os.path.join(os.path.dirname(__file__), "pronom84_idrules_all.json")
    call_command("loaddata", fixture_file, app_label="fpr")

    fixture_file = os.path.join(os.path.dirname(__file__), "pronom84_fprules_all.json")
    call_command("loaddata", fixture_file, app_label="fpr")


class Migration(migrations.Migration):

    dependencies = [("fpr", "0002_initial_data")]

    operations = [migrations.RunPython(load_fixtures)]
