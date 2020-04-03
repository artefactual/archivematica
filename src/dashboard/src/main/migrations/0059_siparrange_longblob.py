# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, OperationalError
import main.models
import django_extensions.db.fields


def drop_original_path_unique_key(apps, schema_editor):
    """Drop the unique key index from `original_path`.

    As the column is becoming a longblog, we need to remove its index to avoid
    issues with the length of the key. The function is implemented so it works
    regardless the name of the index.

    See https://github.com/artefactual/archivematica/pull/1232.
    """
    db_name = schema_editor.connection.settings_dict["NAME"]
    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute(
                "SELECT INDEX_NAME FROM information_schema.STATISTICS"
                " WHERE TABLE_SCHEMA = %s"
                ' AND TABLE_NAME = "main_siparrange"'
                ' AND COLUMN_NAME = "original_path"',
                (db_name,),
            )
        except OperationalError:
            return  # We tried our best.
        row = cursor.fetchone()
        if not row:
            return
        index_name = row[0]
        cursor.execute("ALTER TABLE main_siparrange DROP INDEX %s" % (index_name,))


class Migration(migrations.Migration):

    dependencies = [("main", "0058_fix_unit_variable_pull_link")]

    operations = [
        migrations.RunPython(drop_original_path_unique_key, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="siparrange",
            name="arrange_path",
            field=main.models.BlobTextField(),
        ),
        migrations.AlterField(
            model_name="siparrange",
            name="file_uuid",
            field=django_extensions.db.fields.UUIDField(
                null=True,
                default=None,
                editable=False,
                max_length=36,
                blank=True,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="siparrange",
            name="original_path",
            field=main.models.BlobTextField(default=None, null=True, blank=True),
        ),
    ]
