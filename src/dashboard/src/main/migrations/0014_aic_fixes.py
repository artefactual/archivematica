# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    # Update delete bagged files to continue processing if there's an error
    MicroServiceChainLink.objects.filter(
        id="63f35161-ba76-4a43-8cfa-c38c6a2d5b2f"
    ).update(defaultnextchainlink="7c44c454-e3cc-43d4-abe0-885f93d693c6")
    MicroServiceChainLink.objects.filter(
        id="746b1f47-2dad-427b-8915-8b0cb7acccd8"
    ).update(defaultnextchainlink="7c44c454-e3cc-43d4-abe0-885f93d693c6")


class Migration(migrations.Migration):

    dependencies = [("main", "0013_upload_archivesspace_inherit_notes")]

    operations = [migrations.RunPython(data_migration)]
