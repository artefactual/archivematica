# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0052_correct_extract_packages_fallback_link")]

    operations = [
        migrations.RemoveField(
            model_name="standardtaskconfig", name="requires_output_lock"
        )
    ]
