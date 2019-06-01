# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0067_delete_workflow_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='system_emails',
            field=models.BooleanField(default=False),
        ),
    ]
