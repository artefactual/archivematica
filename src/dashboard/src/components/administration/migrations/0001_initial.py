# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations

import main.models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ArchivistsToolkitConfig",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                ("host", models.CharField(max_length=50)),
                ("port", models.IntegerField(default=3306)),
                ("dbname", models.CharField(max_length=50)),
                ("dbuser", models.CharField(max_length=50)),
                ("dbpass", models.CharField(max_length=50)),
                ("atuser", models.CharField(max_length=50)),
                ("premis", models.CharField(max_length=10)),
                ("ead_actuate", models.CharField(max_length=50)),
                ("ead_show", models.CharField(max_length=50)),
                ("object_type", models.CharField(max_length=50, null=True, blank=True)),
                ("use_statement", models.CharField(max_length=50)),
                ("uri_prefix", models.CharField(max_length=50)),
                (
                    "access_conditions",
                    models.CharField(max_length=50, null=True, blank=True),
                ),
                (
                    "use_conditions",
                    models.CharField(max_length=50, null=True, blank=True),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="ReplacementDict",
            fields=[
                (
                    "id",
                    main.models.UUIDPkField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                    ),
                ),
                ("dictname", models.CharField(max_length=50)),
                ("position", models.IntegerField(default=1)),
                ("parameter", models.CharField(max_length=50)),
                ("displayname", models.CharField(max_length=50)),
                ("displayvalue", models.CharField(max_length=50)),
                ("hidden", models.IntegerField()),
            ],
            options={"db_table": "ReplacementDict"},
            bases=(models.Model,),
        ),
    ]
