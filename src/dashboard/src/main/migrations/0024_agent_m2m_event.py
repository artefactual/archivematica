# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0023_normalization_report'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='linking_agent',
        ),
        migrations.AddField(
            model_name='event',
            name='agents',
            field=models.ManyToManyField(to='main.Agent'),
            preserve_default=True,
        ),
    ]
