# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0026_agent_m2m_event'),
    ]

    operations = [
        migrations.RunSQL('CREATE INDEX Files_currentLocation ON Files(currentLocation(255))')
    ]
