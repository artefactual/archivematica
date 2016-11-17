# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0028_drmc'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transfer',
            name='description',
        ),
        migrations.RemoveField(
            model_name='transfer',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='transfer',
            name='sourceofacquisition',
        ),
        migrations.RemoveField(
            model_name='transfer',
            name='typeoftransfer',
        ),
    ]
