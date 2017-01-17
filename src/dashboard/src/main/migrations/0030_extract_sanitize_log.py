# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def data_migration(apps, schema_editor):
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')
    StandardTaskConfig.objects\
        .filter(id='f368a36d-2b27-4f08-b662-2828a96d189a')\
        .update(stdout_file='%SIPLogsDirectory%filenameCleanup.log',
                stderr_file='%SIPLogsDirectory%filenameCleanup.log')


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_backlog_removal_event'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]
