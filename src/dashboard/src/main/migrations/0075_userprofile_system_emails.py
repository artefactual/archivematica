# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("main", "0074_version_number")]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="system_emails",
            field=models.BooleanField(
                default=True,
                help_text="If checked, this user will receive system emails, such as Transfer Fail and Normalization Reports.",
                verbose_name="Send system emails?",
            ),
        )
    ]
