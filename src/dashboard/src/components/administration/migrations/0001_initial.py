# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import main.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivesSpaceConfig',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('host', models.CharField(max_length=50, verbose_name=b'ArchivesSpace host')),
                ('port', models.IntegerField(default=8089, verbose_name=b'ArchivesSpace backend port')),
                ('user', models.CharField(max_length=50, verbose_name=b'ArchivesSpace administrative user')),
                ('passwd', models.CharField(max_length=50, verbose_name=b'ArchivesSpace administrative user password', blank=True)),
                ('premis', models.CharField(default=b'yes', max_length=10, verbose_name=b'Restrictions Apply', choices=[(b'yes', b'Yes'), (b'no', b'No'), (b'premis', b'Base on PREMIS')])),
                ('xlink_show', models.CharField(default=b'embed', max_length=50, verbose_name=b'XLink Show', choices=[(b'embed', b'Embed'), (b'new', b'New'), (b'none', b'None'), (b'other', b'Other'), (b'replace', b'Replace')])),
                ('xlink_actuate', models.CharField(default=b'none', max_length=50, verbose_name=b'XLink Actuate', choices=[(b'none', b'None'), (b'onLoad', b'onLoad'), (b'other', b'other'), (b'onRequest', b'onRequest')])),
                ('object_type', models.CharField(max_length=50, verbose_name=b'Object type', blank=True)),
                ('use_statement', models.CharField(max_length=50, verbose_name=b'Use statement')),
                ('uri_prefix', models.CharField(max_length=50, verbose_name=b'URL prefix')),
                ('access_conditions', models.CharField(max_length=50, verbose_name=b'Conditions governing access', blank=True)),
                ('use_conditions', models.CharField(max_length=50, verbose_name=b'Conditions governing use', blank=True)),
                ('repository', models.IntegerField(default=2, verbose_name=b'ArchivesSpace repository number')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ArchivistsToolkitConfig',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('host', models.CharField(max_length=50, verbose_name=b'Database Host')),
                ('port', models.IntegerField(default=3306, verbose_name=b'Database Port')),
                ('dbname', models.CharField(max_length=50, verbose_name=b'Database Name')),
                ('dbuser', models.CharField(max_length=50, verbose_name=b'Database User')),
                ('dbpass', models.CharField(max_length=50, verbose_name=b'Database Password', blank=True)),
                ('atuser', models.CharField(max_length=50, verbose_name=b'Archivists Toolkit Username')),
                ('premis', models.CharField(default=b'yes', max_length=10, verbose_name=b'Restrictions Apply', choices=[(b'yes', b'Yes'), (b'no', b'No'), (b'premis', b'Base on PREMIS')])),
                ('ead_actuate', models.CharField(default=b'none', max_length=50, verbose_name=b'EAD DAO Actuate', choices=[(b'none', b'None'), (b'onLoad', b'onLoad'), (b'other', b'other'), (b'onRequest', b'onRequest')])),
                ('ead_show', models.CharField(default=b'embed', max_length=50, verbose_name=b'EAD DAO Show', choices=[(b'embed', b'Embed'), (b'new', b'New'), (b'none', b'None'), (b'other', b'Other'), (b'replace', b'Replace')])),
                ('object_type', models.CharField(max_length=50, verbose_name=b'Object type', blank=True)),
                ('use_statement', models.CharField(max_length=50, verbose_name=b'Use Statement')),
                ('uri_prefix', models.CharField(max_length=50, verbose_name=b'URL prefix')),
                ('access_conditions', models.CharField(max_length=50, verbose_name=b'Conditions governing access', blank=True)),
                ('use_conditions', models.CharField(max_length=50, verbose_name=b'Conditions governing use', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReplacementDict',
            fields=[
                ('id', main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('dictname', models.CharField(max_length=50)),
                ('position', models.IntegerField(default=1)),
                ('parameter', models.CharField(max_length=50)),
                ('displayname', models.CharField(max_length=50)),
                ('displayvalue', models.CharField(max_length=50)),
                ('hidden', models.IntegerField()),
            ],
            options={
                'db_table': 'ReplacementDict',
            },
            bases=(models.Model,),
        ),
    ]
