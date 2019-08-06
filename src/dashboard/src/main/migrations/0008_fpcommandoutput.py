# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0007_django_upgrade_tweaks")]

    def merge_tables(apps, schema_editor):
        cursor = schema_editor.connection.cursor()
        # Check if FPCommandOutput exists
        sql = (
            "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='FPCommandOutput'"
        )
        try:
            cursor.execute(sql)
            contents = cursor.fetchall()
        except Exception:
            return

        # If FPCommandOutput exists, merge
        if contents:
            # Copy to main_fpcommandoutput
            sql = "INSERT main_fpcommandoutput (fileUUID, content, ruleUUID) SELECT fileUUID, content, ruleUUID FROM FPCommandOutput"
            cursor.execute(sql)

        # TODO delete FPCommandOutput

    operations = [migrations.RunPython(merge_tables)]
