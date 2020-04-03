# -*- coding: utf-8 -*-

"""MySQL specific indexes for Files."""
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def create_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "CREATE INDEX Files_transfer_lvrgv3pn_idx ON Files (transferUUID, currentLocation(767));"
        )
        cursor.execute(
            "CREATE INDEX Files_transfer_bru5if1u_idx ON Files (transferUUID, originalLocation(767));"
        )
        cursor.execute(
            "CREATE INDEX Files_sip_1x6rkqbm_idx ON Files (sipUUID, currentLocation(767));"
        )
        cursor.execute(
            "CREATE INDEX Files_sip_orpn8lfh_idx ON Files (sipUUID, originalLocation(767));"
        )


def drop_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX Files_transfer_lvrgv3pn_idx ON Files;")
        cursor.execute("DROP INDEX Files_transfer_bru5if1u_idx ON Files;")
        cursor.execute("DROP INDEX Files_sip_1x6rkqbm_idx ON Files;")
        cursor.execute("DROP INDEX Files_sip_orpn8lfh_idx ON Files;")


class Migration(migrations.Migration):
    dependencies = [("main", "0072_index_files")]

    operations = [migrations.RunPython(create_indexes, drop_indexes, atomic=True)]
