# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_clean_transfers'),
        ('main', '0029_backlog_removal_event'),  # Merge parallel paths of migrations
    ]

    operations = [
        migrations.AddField(
            model_name='transfer',
            name='access_system_id',
            field=models.TextField(default='', db_column=b'access_system_id'),
            preserve_default=False,
        ),
    ]
