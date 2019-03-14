# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0002_initial_data")]

    operations = [
        migrations.CreateModel(
            name="ArchivesSpaceDIPObjectResourcePairing",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False, primary_key=True, db_column=b"pk"
                    ),
                ),
                ("dipuuid", models.CharField(max_length=50, db_column=b"dipUUID")),
                ("fileuuid", models.CharField(max_length=50, db_column=b"fileUUID")),
                (
                    "resourceid",
                    models.CharField(max_length=150, db_column=b"resourceId"),
                ),
            ],
            options={
                "db_table": "ArchivesSpaceDIPObjectResourcePairing",
                "verbose_name": "ASDIPObjectResourcePairing",
            },
            bases=(models.Model,),
        )
    ]
