# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def data_migration(apps, schema_editor):
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')

    # Add SIPUUID argument to restructureForCompliance_v0.0
    StandardTaskConfig.objects.filter(execute='restructureForCompliance_v0.0').update(arguments='"%SIPDirectory%" "%SIPUUID%"')

    # Add sharedPath argument to updateSizeAndChecksum_v0.0
    StandardTaskConfig.objects.filter(execute='updateSizeAndChecksum_v0.0').update(arguments='"%sharedPath%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"')


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0026_agent_m2m_event'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]
