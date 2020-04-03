# -*- coding: utf-8 -*-

"""A MySQL specific index for UnitVariables."""
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def create_index(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "CREATE INDEX UnitVariables_ep46xp7f_idx ON UnitVariables (unitUUID, unitType, variable(255));"
        )


def drop_index(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX UnitVariables_ep46xp7f_idx ON UnitVariables;")


class Migration(migrations.Migration):

    dependencies = [("main", "0070_index_jobs")]

    # MySQL specific syntax
    operations = [migrations.RunPython(create_index, drop_index, atomic=True)]
