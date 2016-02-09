# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_django_upgrade_tweaks'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='fpcommandoutput',
            table='FPCommandOutput',
        ),
    ]
