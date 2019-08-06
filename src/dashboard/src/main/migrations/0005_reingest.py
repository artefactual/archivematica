# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0004_rights")]

    operations = [
        migrations.AddField(
            model_name="dublincore",
            name="status",
            field=models.CharField(
                default="ORIGINAL",
                max_length=8,
                db_column="status",
                choices=[
                    ("ORIGINAL", "original"),
                    ("REINGEST", "parsed from reingest"),
                    ("UPDATED", "updated"),
                ],
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="rightsstatement",
            name="status",
            field=models.CharField(
                default="ORIGINAL",
                max_length=8,
                db_column="status",
                choices=[
                    ("ORIGINAL", "original"),
                    ("REINGEST", "parsed from reingest"),
                    ("UPDATED", "updated"),
                ],
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="dublincore",
            name="metadataappliestoidentifier",
            field=models.CharField(
                default=None,
                max_length=36,
                null=True,
                db_column="metadataAppliesToidentifier",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="sip",
            name="createdtime",
            field=models.DateTimeField(auto_now_add=True, db_column="createdTime"),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="sip",
            name="sip_type",
            field=models.CharField(
                default="SIP",
                max_length=8,
                db_column="sipType",
                choices=[
                    ("SIP", "SIP"),
                    ("AIC", "AIC"),
                    ("AIP-REIN", "Reingested AIP"),
                    ("AIC-REIN", "Reingested AIC"),
                ],
            ),
            preserve_default=True,
        ),
    ]
