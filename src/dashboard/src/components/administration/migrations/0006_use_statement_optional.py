# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("administration", "0005_archivesspace_inherit_note_default")]

    operations = [
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="use_statement",
            field=models.CharField(
                help_text=b"Optional, but if present should come from ArchivesSpace controlled list. Example: image-master",
                max_length=50,
                verbose_name=b"Use statement",
                blank=True,
            ),
        )
    ]
