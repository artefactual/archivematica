# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("fpr", "0026_fits_nailgun_compat")]

    operations = [
        migrations.AlterField(
            model_name="idcommand",
            name="tool",
            field=models.ForeignKey(
                verbose_name="the related tool",
                to_field="uuid",
                to="fpr.IDTool",
                null=True,
                on_delete=models.CASCADE,
            ),
        )
    ]
