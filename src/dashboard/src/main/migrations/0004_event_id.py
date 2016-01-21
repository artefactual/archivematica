# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_appraisal_tab'),
    ]

    operations = [
        migrations.AlterField(
            model_name='derivation',
            name='event',
            field=models.ForeignKey(db_column=b'relatedEventUUID', blank=True, to='main.Event', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='event_id',
            field=django_extensions.db.fields.UUIDField(max_length=36, null=True, editable=False, db_column=b'eventIdentifierUUID', blank=True),
            preserve_default=True,
        ),
    ]
