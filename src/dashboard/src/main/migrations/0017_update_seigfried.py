# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    mscrd = apps.get_model("main", "MicroServiceChoiceReplacementDic")

    # make the Seigfried replacementDics point at a new IDCommand for sf 1.5.0
    # see archivematica-fpr-admin branch 1.1.x

    mscrd.objects.filter(id="bed4eeb1-d654-4d97-b98d-40eb51d3d4bb").update(
        replacementdic='{"%IDCommand%":"9d2cefc1-2bd2-44e4-8d55-6cf8151eecff"}'
    )
    mscrd.objects.filter(id="664cbde3-e658-4288-87db-bd28266d83f5").update(
        replacementdic='{"%IDCommand%":"9d2cefc1-2bd2-44e4-8d55-6cf8151eecff"}'
    )
    mscrd.objects.filter(id="25a91595-37f0-4373-a89a-56a757353fb8").update(
        replacementdic='{"%IDCommand%":"9d2cefc1-2bd2-44e4-8d55-6cf8151eecff"}'
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0016_file_currentlocation_nullable")]

    operations = [migrations.RunPython(data_migration)]
