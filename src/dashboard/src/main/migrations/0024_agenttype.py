# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("main", "0023_blob_fields")]

    operations = [
        migrations.AlterField(
            model_name="agent",
            name="agenttype",
            field=models.TextField(
                default="organization",
                help_text="Used for premis:agentType in the METS file.",
                verbose_name="Agent Type",
                db_column="agentType",
            ),
        )
    ]
