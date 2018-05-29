# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def data_migration_update_api_whitelist(apps, schema_editor):
    DashboardSetting = apps.get_model('main', 'DashboardSetting')
    DashboardSetting.objects.update_or_create(name='api_whitelist', defaults={'value': ''})


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0032_dashboardsetting_scope'),
    ]

    operations = [
        migrations.RunPython(data_migration_update_api_whitelist),
    ]
