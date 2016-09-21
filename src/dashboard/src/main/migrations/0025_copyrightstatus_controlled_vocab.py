# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0024_agenttype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rightsstatementcopyright',
            name='copyrightstatus',
            field=models.TextField(default=b'unknown', verbose_name=b'Copyright status', db_column=b'copyrightStatus', choices=[(b'copyrighted', b'copyrighted'), (b'public domain', b'public domain'), (b'unknown', b'unknown')]),
        ),
    ]
