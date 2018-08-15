# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [
        ('fpr', '0017_ocr_unique_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='format',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from=b'description', unique=True, verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='formatgroup',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from=b'description', unique=True, verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='fptool',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from=b'_slug', unique=True, verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='idtool',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from=b'_slug', always_update=True, unique=True, verbose_name='slug'),
        ),
    ]
