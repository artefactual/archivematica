# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration_up(apps, schema_editor):
    """
    Change filegrpuse of pointer files:

    In AM 1.6, the pointer file was being created in the MCPClient and added
    to the SIP files with the default filegrpuse: 'original'. This was making
    this file to appear, named 'xml', in the normalization reports as an
    error. This file should have been added to the SIP files with
    'submissionDocumentation' as its filegrpuse and changing it in this
    migration will make them disappear from existing reports.
    """
    update_pointer_files_filegrpuse(apps, "submissionDocumentation")


def data_migration_down(apps, schema_editor):
    """Restore previous filegrpuse value of pointer files."""
    update_pointer_files_filegrpuse(apps, "original")


def update_pointer_files_filegrpuse(apps, filegrpuse):
    """Change filegrpuse of existing pointer files."""
    File = apps.get_model("main", "File")
    location = "%SIPDirectory%pointer.xml"
    pointer_files = File.objects.filter(
        originallocation=location, currentlocation=location
    )
    if pointer_files.exists():
        pointer_files.update(filegrpuse=filegrpuse)


class Migration(migrations.Migration):

    dependencies = [("main", "0048_fix_upload_qubit_setting")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
