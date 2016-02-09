# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_reingest'),
    ]

    operations = [
        migrations.CreateModel(
            name='LevelOfDescription',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('name', models.CharField(max_length=b'1024')),
                ('sortorder', models.IntegerField(default=0, db_column=b'sortOrder')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='siparrange',
            name='level_of_description',
            field=models.CharField(default='', max_length=2014),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='siparrange',
            name='sip',
            field=models.ForeignKey(default=None, blank=True, to='main.SIP', null=True),
            preserve_default=True,
        ),
    ]
