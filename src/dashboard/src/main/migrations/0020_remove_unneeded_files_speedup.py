# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def data_migration(apps, schema_editor):
    TaskConfig = apps.get_model('main', 'TaskConfig')
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')

    one_instance_task_type = '36b2e239-4a57-4aa5-8ebc-7a29139baca6'
    date_modified = '2016-08-19T16:09:53+00:00'

    # Update removeUnneededFiles and removeCacheFiles to run once per ingest.
    TaskConfig.objects.filter(pk='85308c8b-b299-4453-bf40-9ac61d134015').update(tasktype=one_instance_task_type)
    TaskConfig.objects.filter(pk='85308c8b-b299-4453-bf40-9ac61d134015').update(lastmodified=date_modified)
    TaskConfig.objects.filter(pk='ef0bb0cf-28d5-4687-a13d-2377341371b5').update(tasktype=one_instance_task_type)
    TaskConfig.objects.filter(pk='ef0bb0cf-28d5-4687-a13d-2377341371b5').update(lastmodified=date_modified)

    # Update standardTaskConfig to get called with the Objects Directory and UUID for the SIP
    StandardTaskConfig.objects.filter(pk='49b803e3-8342-4098-bb3f-434e1eb5cfa8').update(arguments='"%SIPDirectory%" "%SIPUUID%"')
    StandardTaskConfig.objects.filter(pk='49b803e3-8342-4098-bb3f-434e1eb5cfa8').update(lastmodified=date_modified)
    StandardTaskConfig.objects.filter(pk='66aa823d-3b72-4d13-9ad6-c5e6580857b8').update(arguments='"%SIPDirectory%" "%SIPUUID%"')
    StandardTaskConfig.objects.filter(pk='66aa823d-3b72-4d13-9ad6-c5e6580857b8 ').update(lastmodified=date_modified)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_normalization_report'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]
