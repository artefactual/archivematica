# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Migration that causes each OCR text file to include the UUID of its
    source file in its filename. This prevents OCR text files from overwriting
    one another when there are two identically named source files in a
    transfer. See
    https://github.com/artefactual/archivematica-fpr-admin/issues/66
    """
    FPCommand = apps.get_model("fpr", "FPCommand")
    ocr_command = FPCommand.objects.get(uuid="4ea06c2b-ee42-4f80-ad10-4e044ba0676a")
    ocr_command.command = (
        'ocrfiles="%SIPObjectsDirectory%metadata/OCRfiles"\n'
        'test -d "$ocrfiles" || mkdir -p "$ocrfiles"\n\n'
        'tesseract %fileFullName% "$ocrfiles/%fileName%-%fileUUID%"'
    )
    ocr_command.output_location = (
        "%SIPObjectsDirectory%metadata/OCRfiles/%fileName%-%fileUUID%.txt"
    )
    ocr_command.save()


class Migration(migrations.Migration):

    dependencies = [("fpr", "0016_update_idtools")]

    operations = [migrations.RunPython(data_migration)]
