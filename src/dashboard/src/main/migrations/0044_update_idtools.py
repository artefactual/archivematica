# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    mscrd = apps.get_model("main", "MicroServiceChoiceReplacementDic")

    # Use new fido command introduced in fpr-admin v1.7.2
    fido_idcommand_ids = [
        "0db6372b-f507-4db0-9993-e745044a69f9",
        "56345ae4-08d1-42df-a2f9-9ba37689d9c3",
        "6f9bfd67-f598-400a-aa2e-12b2657962fc",
    ]
    mscrd.objects.filter(id__in=fido_idcommand_ids).update(
        replacementdic='{"%IDCommand%":"76006ad7-a401-48f6-98f6-2efc01003276"}'
    )

    # Use new siegfried command introduced in fpr-admin v1.7.2
    siegfried_idcommand_ids = [
        "25a91595-37f0-4373-a89a-56a757353fb8",
        "664cbde3-e658-4288-87db-bd28266d83f5",
        "bed4eeb1-d654-4d97-b98d-40eb51d3d4bb",
    ]
    mscrd.objects.filter(id__in=siegfried_idcommand_ids).update(
        replacementdic='{"%IDCommand%":"df074736-e2f7-4102-b25d-569c099d410c"}'
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0043_remove_create_pointer_file_ms")]

    operations = [migrations.RunPython(data_migration)]
