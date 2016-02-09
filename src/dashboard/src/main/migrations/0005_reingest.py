# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_rights'),
    ]

    operations = [
        migrations.AddField(
            model_name='dublincore',
            name='status',
            field=models.CharField(default=b'ORIGINAL', max_length=8, db_column=b'status', choices=[(b'ORIGINAL', b'original'), (b'REINGEST', b'parsed from reingest'), (b'UPDATED', b'updated')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rightsstatement',
            name='status',
            field=models.CharField(default=b'ORIGINAL', max_length=8, db_column=b'status', choices=[(b'ORIGINAL', b'original'), (b'REINGEST', b'parsed from reingest'), (b'UPDATED', b'updated')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dublincore',
            name='metadataappliestoidentifier',
            field=models.CharField(default=None, max_length=36, null=True, db_column=b'metadataAppliesToidentifier', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sip',
            name='createdtime',
            field=models.DateTimeField(auto_now_add=True, db_column=b'createdTime'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sip',
            name='sip_type',
            field=models.CharField(default=b'SIP', max_length=8, db_column=b'sipType', choices=[(b'SIP', b'SIP'), (b'AIC', b'AIC'), (b'AIP-REIN', b'Reingested AIP'), (b'AIC-REIN', b'Reingested AIC')]),
            preserve_default=True,
        ),
    ]
