# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    MicroServiceChoiceReplacementDic = apps.get_model('main', 'MicroServiceChoiceReplacementDic')

    # Modify user choice to indicate use of lbzip2 instead of pbzip2.
    newAipCompressionAlgorithmString = '{"%AIPCompressionAlgorithm%":"lbzip2-"}'
    MicroServiceChoiceReplacementDic.objects.filter(pk='f61b00a1-ef2e-4dc4-9391-111c6f42b9a7').update(replacementdic=newAipCompressionAlgorithmString)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0021_remove_update_checksum'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]
