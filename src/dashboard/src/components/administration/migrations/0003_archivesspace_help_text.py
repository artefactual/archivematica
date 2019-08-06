# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("administration", "0002_archivesspaceconfig")]

    operations = [
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="access_conditions",
            field=models.CharField(
                help_text=b"Populates Conditions governing access note",
                max_length=50,
                verbose_name=b"Conditions governing access",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="host",
            field=models.CharField(
                help_text=b"Do not include http:// or www. Example: aspace.test.org ",
                max_length=50,
                verbose_name=b"ArchivesSpace host",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="object_type",
            field=models.CharField(
                help_text=b"Optional, must come from ArchivesSpace controlled list. Example: sound_recording",
                max_length=50,
                verbose_name=b"Object type",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="passwd",
            field=models.CharField(
                help_text=b"Password for user set above. Re-enter this password every time changes are made.",
                max_length=50,
                verbose_name=b"ArchivesSpace administrative user password",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="port",
            field=models.IntegerField(
                default=8089,
                help_text=b"Example: 8089",
                verbose_name=b"ArchivesSpace backend port",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="repository",
            field=models.IntegerField(
                default=2,
                help_text=b"Default for single repository installation is 2",
                verbose_name=b"ArchivesSpace repository number",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="uri_prefix",
            field=models.CharField(
                help_text=b"URL of DIP object server as you wish to appear in ArchivesSpace record. Example: http://example.com",
                max_length=50,
                verbose_name=b"URL prefix",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="use_conditions",
            field=models.CharField(
                help_text=b"Populates Conditions governing use note",
                max_length=50,
                verbose_name=b"Conditions governing use",
                blank=True,
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="use_statement",
            field=models.CharField(
                help_text=b"Mandatory, must come from ArchivesSpace controlled list. Example: image-master",
                max_length=50,
                verbose_name=b"Use statement",
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="archivesspaceconfig",
            name="user",
            field=models.CharField(
                help_text=b"Example: admin",
                max_length=50,
                verbose_name=b"ArchivesSpace administrative user",
            ),
            preserve_default=True,
        ),
    ]
