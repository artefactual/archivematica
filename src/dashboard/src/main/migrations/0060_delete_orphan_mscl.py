# -*- coding: utf-8 -*-
"""Migration for the deletion of an orphan chain link in the workflow."""
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def delete_orphan_mscl(apps, schema_editor):
    """Delete orphan chain link "Index transfer contents".

    It was left behind in migration `0020`.
    """
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")

    index_transfer_contents_mscl_id = "eb52299b-9ae6-4a1f-831e-c7eee0de829f"

    MicroServiceChainLink.objects.filter(id=index_transfer_contents_mscl_id).delete()


class Migration(migrations.Migration):

    dependencies = [("main", "0059_siparrange_longblob")]

    operations = [migrations.RunPython(delete_orphan_mscl, migrations.RunPython.noop)]
