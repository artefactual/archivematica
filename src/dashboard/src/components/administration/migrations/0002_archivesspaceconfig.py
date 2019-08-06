# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations

import main.models


def insert_data(apps, schema_editor):
    # Insert default values into the ArchivesSpaceConfig table.
    # Leaving all other values null/blank is consistent with default ATK config.
    ArchivesSpaceConfig = apps.get_model("administration", "ArchivesSpaceConfig")
    ArchivesSpaceConfig.objects.create(
        pk="5e6b9fb2-0ed0-41c4-b5cb-94d25de1a5dc", port=8089, repository=2
    )


class Migration(migrations.Migration):

    dependencies = [("administration", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ArchivesSpaceConfig",
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
                (
                    "host",
                    models.CharField(max_length=50, verbose_name=b"ArchivesSpace host"),
                ),
                (
                    "port",
                    models.IntegerField(
                        default=8089, verbose_name=b"ArchivesSpace backend port"
                    ),
                ),
                (
                    "user",
                    models.CharField(
                        max_length=50, verbose_name=b"ArchivesSpace administrative user"
                    ),
                ),
                (
                    "passwd",
                    models.CharField(
                        max_length=50,
                        verbose_name=b"ArchivesSpace administrative user password",
                        blank=True,
                    ),
                ),
                (
                    "premis",
                    models.CharField(
                        default=b"yes",
                        max_length=10,
                        verbose_name=b"Restrictions Apply",
                        choices=[
                            (b"yes", b"Yes"),
                            (b"no", b"No"),
                            (b"premis", b"Base on PREMIS"),
                        ],
                    ),
                ),
                (
                    "xlink_show",
                    models.CharField(
                        default=b"embed",
                        max_length=50,
                        verbose_name=b"XLink Show",
                        choices=[
                            (b"embed", b"Embed"),
                            (b"new", b"New"),
                            (b"none", b"None"),
                            (b"other", b"Other"),
                            (b"replace", b"Replace"),
                        ],
                    ),
                ),
                (
                    "xlink_actuate",
                    models.CharField(
                        default=b"none",
                        max_length=50,
                        verbose_name=b"XLink Actuate",
                        choices=[
                            (b"none", b"None"),
                            (b"onLoad", b"onLoad"),
                            (b"other", b"other"),
                            (b"onRequest", b"onRequest"),
                        ],
                    ),
                ),
                (
                    "object_type",
                    models.CharField(
                        max_length=50, verbose_name=b"Object type", blank=True
                    ),
                ),
                (
                    "use_statement",
                    models.CharField(max_length=50, verbose_name=b"Use statement"),
                ),
                (
                    "uri_prefix",
                    models.CharField(max_length=50, verbose_name=b"URL prefix"),
                ),
                (
                    "access_conditions",
                    models.CharField(
                        max_length=50,
                        verbose_name=b"Conditions governing access",
                        blank=True,
                    ),
                ),
                (
                    "use_conditions",
                    models.CharField(
                        max_length=50,
                        verbose_name=b"Conditions governing use",
                        blank=True,
                    ),
                ),
                (
                    "repository",
                    models.IntegerField(
                        default=2, verbose_name=b"ArchivesSpace repository number"
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="access_conditions",
            field=models.CharField(
                default="",
                max_length=50,
                verbose_name=b"Conditions governing access",
                blank=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="atuser",
            field=models.CharField(
                max_length=50, verbose_name=b"Archivists Toolkit Username"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="dbname",
            field=models.CharField(max_length=50, verbose_name=b"Database Name"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="dbpass",
            field=models.CharField(
                max_length=50, verbose_name=b"Database Password", blank=True
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="dbuser",
            field=models.CharField(max_length=50, verbose_name=b"Database User"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="ead_actuate",
            field=models.CharField(
                default=b"none",
                max_length=50,
                verbose_name=b"EAD DAO Actuate",
                choices=[
                    (b"none", b"None"),
                    (b"onLoad", b"onLoad"),
                    (b"other", b"other"),
                    (b"onRequest", b"onRequest"),
                ],
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="ead_show",
            field=models.CharField(
                default=b"embed",
                max_length=50,
                verbose_name=b"EAD DAO Show",
                choices=[
                    (b"embed", b"Embed"),
                    (b"new", b"New"),
                    (b"none", b"None"),
                    (b"other", b"Other"),
                    (b"replace", b"Replace"),
                ],
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="host",
            field=models.CharField(max_length=50, verbose_name=b"Database Host"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="object_type",
            field=models.CharField(
                default="", max_length=50, verbose_name=b"Object type", blank=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="port",
            field=models.IntegerField(default=3306, verbose_name=b"Database Port"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="premis",
            field=models.CharField(
                default=b"yes",
                max_length=10,
                verbose_name=b"Restrictions Apply",
                choices=[
                    (b"yes", b"Yes"),
                    (b"no", b"No"),
                    (b"premis", b"Base on PREMIS"),
                ],
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="uri_prefix",
            field=models.CharField(max_length=50, verbose_name=b"URL prefix"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="use_conditions",
            field=models.CharField(
                default="",
                max_length=50,
                verbose_name=b"Conditions governing use",
                blank=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="archiviststoolkitconfig",
            name="use_statement",
            field=models.CharField(max_length=50, verbose_name=b"Use Statement"),
            preserve_default=True,
        ),
        migrations.RunPython(insert_data),
    ]
