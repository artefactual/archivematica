# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("administration", "0003_archivesspace_help_text")]

    operations = [
        migrations.AddField(
            model_name="archivesspaceconfig",
            name="inherit_notes",
            field=models.BooleanField(
                default=False,
                verbose_name=b"Inherit digital object notes from the parent component",
            ),
            preserve_default=True,
        )
    ]
