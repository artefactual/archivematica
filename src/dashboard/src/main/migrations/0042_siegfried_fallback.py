# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def data_migration(apps, schema_editor):
    mscrd = apps.get_model('main', 'MicroServiceChoiceReplacementDic')
    # Make the Siegfried replacementDics point at a new IDCommand, one which
    # falls back to blkid if Siegfried returns 'UNKNOWN'.
    mscrd.objects.filter(id='bed4eeb1-d654-4d97-b98d-40eb51d3d4bb').update(
        replacementdic='{"%IDCommand%":"b8a39a9a-3fd9-4519-8f2c-c5247cc36ecf"}')
    mscrd.objects.filter(id='664cbde3-e658-4288-87db-bd28266d83f5').update(
        replacementdic='{"%IDCommand%":"b8a39a9a-3fd9-4519-8f2c-c5247cc36ecf"}')
    mscrd.objects.filter(id='25a91595-37f0-4373-a89a-56a757353fb8').update(
        replacementdic='{"%IDCommand%":"b8a39a9a-3fd9-4519-8f2c-c5247cc36ecf"}')


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0041_bind_pids'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]
