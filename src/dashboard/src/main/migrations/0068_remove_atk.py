# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0067_delete_workflow_models'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AtkDIPObjectResourcePairing',
        ),
        migrations.AlterField(
            model_name='siparrangeaccessmapping',
            name='system',
            field=models.CharField(default=b'atom', max_length=255, choices=[(b'archivesspace', b'ArchivesSpace'), (b'atom', b'AtoM')]),
        ),
    ]
