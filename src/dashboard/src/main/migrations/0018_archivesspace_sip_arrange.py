# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0017_update_seigfried")]

    operations = [
        migrations.CreateModel(
            name="ArchivesSpaceDigitalObject",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("resourceid", models.CharField(max_length=150)),
                ("label", models.CharField(max_length=255, blank=True)),
                ("title", models.TextField(blank=True)),
                (
                    "started",
                    models.BooleanField(
                        default=False,
                        help_text="Whether or not a SIP has been started using files in this digital object.",
                    ),
                ),
                (
                    "remoteid",
                    models.CharField(
                        help_text="ID in the remote ArchivesSpace system, after digital object has been created.",
                        max_length=150,
                        blank=True,
                    ),
                ),
                (
                    "sip",
                    models.ForeignKey(
                        to="main.SIP", null=True, on_delete=models.CASCADE
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SIPArrangeAccessMapping",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("arrange_path", models.CharField(max_length=255)),
                (
                    "system",
                    models.CharField(
                        default="atom",
                        max_length=255,
                        choices=[
                            ("archivesspace", "ArchivesSpace"),
                            ("atk", "Archivist's Toolkit"),
                            ("atom", "AtoM"),
                        ],
                    ),
                ),
                ("identifier", models.CharField(max_length=255)),
            ],
        ),
    ]
