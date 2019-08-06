# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("main", "0024_agenttype")]

    operations = [
        migrations.AlterField(
            model_name="rightsstatementcopyright",
            name="copyrightstatus",
            field=models.TextField(
                default="unknown",
                verbose_name="Copyright status",
                db_column="copyrightStatus",
                choices=[
                    ("copyrighted", "copyrighted"),
                    ("public domain", "public domain"),
                    ("unknown", "unknown"),
                ],
            ),
        )
    ]
