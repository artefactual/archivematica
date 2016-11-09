# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_update_seigfried'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivesSpaceDigitalObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resourceid', models.CharField(max_length=150)),
                ('label', models.CharField(max_length=255, blank=True)),
                ('title', models.TextField(blank=True)),
                ('started', models.BooleanField(default=False, help_text=b'Whether or not a SIP has been started using files in this digital object.')),
                ('remoteid', models.CharField(help_text=b'ID in the remote ArchivesSpace system, after digital object has been created.', max_length=150, blank=True)),
                ('sip', models.ForeignKey(to='main.SIP', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SIPArrangeAccessMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('arrange_path', models.CharField(max_length=255)),
                ('system', models.CharField(default=b'atom', max_length=255, choices=[(b'archivesspace', b'ArchivesSpace'), (b'atk', b"Archivist's Toolkit"), (b'atom', b'AtoM')])),
                ('identifier', models.CharField(max_length=255)),
            ],
        ),
    ]
