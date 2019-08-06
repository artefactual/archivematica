# -*- coding: utf-8 -*-
"""Make Siegfried the default IDCommand.

We've changed file format identification commands so only one object can be
enabled. This migration makes Siegfried the new default.
"""
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration_up(apps, schema_editor):
    IDCommand = apps.get_model("fpr", "IDCommand")

    # Disable all commands available.
    IDCommand.objects.update(enabled=False)

    # Make Siegfried the default (as long as it's available).
    IDCommand.objects.filter(uuid="75290b14-2931-455f-bdde-3b4b3f8b7f15").update(
        enabled=True
    )

    # Cleanup: mark old commands as replaced.
    for new_uuid, prev_uuid in (
        (
            "76006ad7-a401-48f6-98f6-2efc01003276",
            "a8e45bc1-eb35-4545-885c-dd552f1fde9a",
        ),
        (
            "6fa7b8d8-10f1-439d-888a-5ccb3a5be492",
            "76006ad7-a401-48f6-98f6-2efc01003276",
        ),
        (
            "e586f750-6230-42d7-8d12-1e24ca2aa658",
            "6fa7b8d8-10f1-439d-888a-5ccb3a5be492",
        ),
        (
            "213d1589-c255-474f-81ac-f0a618181e40",
            "e586f750-6230-42d7-8d12-1e24ca2aa658",
        ),
        (
            "df074736-e2f7-4102-b25d-569c099d410c",
            "9d2cefc1-2bd2-44e4-8d55-6cf8151eecff",
        ),
        (
            "75290b14-2931-455f-bdde-3b4b3f8b7f15",
            "df074736-e2f7-4102-b25d-569c099d410c",
        ),
    ):
        IDCommand.objects.filter(uuid=new_uuid).update(replaces_id=prev_uuid)


class Migration(migrations.Migration):

    dependencies = [("fpr", "0027_idcommand_tool_disallow_blank")]

    operations = [migrations.RunPython(data_migration_up, migrations.RunPython.noop)]
