# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("main", "0071_index_unitvariables_runsql")]

    operations = [
        migrations.AlterIndexTogether(
            name="file", index_together=set([("sip", "filegrpuse")])
        )
    ]
