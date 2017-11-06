# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def data_migration(apps, schema_editor):
    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')

    MicroServiceChainLink.objects.filter(defaultexitmessage='Failed') \
        .update(defaultexitmessage=4)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0044_update_idtools'),
    ]

    operations = [
        migrations.RunPython(data_migration),
        migrations.AlterField(
            model_name='microservicechainlink',
            name='defaultexitmessage',
            field=models.CharField(default=4, max_length=36, db_column=b'defaultExitMessage', choices=[(0, 'Unknown'), (1, 'Awaiting decision'), (2, 'Completed successfully'), (3, 'Executing command(s)'), (4, 'Failed')]),
        ),
        migrations.AlterField(
            model_name='microservicechainlinkexitcode',
            name='exitmessage',
            field=models.CharField(default=2, max_length=50, db_column=b'exitMessage', choices=[(0, 'Unknown'), (1, 'Awaiting decision'), (2, 'Completed successfully'), (3, 'Executing command(s)'), (4, 'Failed')]),
        ),
    ]
