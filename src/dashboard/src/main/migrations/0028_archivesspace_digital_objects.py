# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_full_reingest'),
    ]

    operations = [
        migrations.RenameModel('ArchivesSpaceDOComponent', 'ArchivesSpaceDigitalObject'),
        migrations.RemoveField(
            model_name='archivesspacedigitalobject',
            name='digitalobjectid',
        ),
        migrations.AlterField(
            model_name='archivesspacedigitalobject',
            name='remoteid',
            field=models.CharField(help_text=b'ID in the remote ArchivesSpace system, after digital object has been created.', max_length=150, blank=True),
        ),
        migrations.AlterField(
            model_name='archivesspacedigitalobject',
            name='started',
            field=models.BooleanField(default=False, help_text=b'Whether or not a SIP has been started using files in this digital object.'),
        ),
    ]
