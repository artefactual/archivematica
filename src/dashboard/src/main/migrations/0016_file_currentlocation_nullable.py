# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0015_no_normalize_thumbnails")]

    operations = [
        migrations.AlterField(
            model_name="file",
            name="currentlocation",
            field=models.TextField(null=True, db_column="currentLocation"),
            preserve_default=True,
        )
    ]
