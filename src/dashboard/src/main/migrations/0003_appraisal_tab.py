# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivesSpaceDOComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resourceid', models.CharField(max_length=150)),
                ('label', models.CharField(max_length=255, blank=True)),
                ('title', models.TextField(blank=True)),
                ('started', models.BooleanField(default=False, help_text=b'Whether or not a SIP has been started using files in this digital object component.')),
                ('digitalobjectid', models.CharField(help_text=b'ID in the remote ArchivesSpace system of the digital object to which this object is parented.', max_length=150, blank=True)),
                ('remoteid', models.CharField(help_text=b'ID in the remote ArchivesSpace system, after component has been created.', max_length=150, blank=True)),
                ('sip', models.ForeignKey(to='main.SIP', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SIPArrangeAccessMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('arrange_path', models.CharField(max_length=255)),
                ('system', models.CharField(default=b'atom', max_length=255, choices=[(b'archivesspace', b'ArchivesSpace'), (b'atk', b"Archivist's Toolkit"), (b'atom', b'AtoM')])),
                ('identifier', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='file',
            name='checksumtype',
            field=models.CharField(max_length=36, db_column=b'checksumType', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='file',
            name='currentlocation',
            field=models.TextField(null=True, db_column=b'currentLocation'),
            preserve_default=True,
        ),
    ]
