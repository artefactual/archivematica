# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations

import main.models


def data_migration(apps, schema_editor):
    # Set AtoM DIP upload defaults
    DashboardSetting = apps.get_model("main", "DashboardSetting")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")

    DashboardSetting.objects.create(
        name="dip_upload_atom_url", value="http://localhost/atom"
    )
    DashboardSetting.objects.create(
        name="dip_upload_atom_email", value="demo@example.com"
    )
    DashboardSetting.objects.create(name="dip_upload_atom_password", value="demo")
    DashboardSetting.objects.create(name="dip_upload_atom_version", value="2")

    StandardTaskConfig.objects.filter(id="ee80b69b-6128-4e31-9db4-ef90aa677c87").update(
        arguments="""--url=\"http://localhost/atom/index.php\" \\\r\n--email=\"demo@example.com\" \\\r\n--password=\"demo\" \\\r\n--uuid=\"%SIPUUID%\" \\\r\n--rsync-target=\"/tmp\" --version=2"""
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0005_reingest_data")]

    operations = [
        migrations.CreateModel(
            name="LevelOfDescription",
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
                ("name", models.CharField(max_length=1024)),
                ("sortorder", models.IntegerField(default=0, db_column="sortOrder")),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="siparrange",
            name="level_of_description",
            field=models.CharField(default="", max_length=2014),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="siparrange",
            name="sip",
            field=models.ForeignKey(
                default=None,
                blank=True,
                to="main.SIP",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.RunPython(data_migration),
    ]
