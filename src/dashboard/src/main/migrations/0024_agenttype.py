# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0023_blob_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='agenttype',
            field=models.TextField(default=b'organization', help_text=b'Used for premis:agentType in the METS file.', verbose_name=b'Agent Type', db_column=b'agentType'),
        ),
    ]
