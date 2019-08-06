# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


OLD_FITS_CMD_UUID = "0b0d301f-b586-45d5-ba35-d76da57ce32a"
NEW_FITS_CMD_UUID = "1a0394dc-528b-4a03-8c2b-1c158f1fb313"
OLD_FITS_RULE_UUID = "296a131d-ce70-45ae-b800-6c71b3ea46f0"
NEW_FITS_RULE_UUID = "c3b06895-ef9d-401e-8c51-ac585f955655"


def data_migration_up(apps, schema_editor):
    """Replace the FITS command with one that is compatible with environments
    where the Nailgun binary is called either `ng` or `nailgun-ng`.
    """
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    fits_tool_uuid = "c5465b07-8dc7-475e-a5c9-ccb2ba2ed083"
    xml_format_uuid = "d60e5243-692e-4af7-90cd-40c53cb8dc7d"
    unknown_format_uuid = "0ab4cd40-90e7-4d75-b294-498177b3897d"

    FPCommand.objects.filter(uuid=OLD_FITS_CMD_UUID).update(enabled=False)

    new_cmd = (
        "set -euo pipefail\n"
        "IFS=$'\\n\\t'\n"
        "tempdir=$(mktemp -d %tmpDirectory%fits.XXXXXX)\n"
        "if type ng-nailgun 1>/dev/null 2>/dev/null\n"
        ' then function ng { ng-nailgun "$@"; }\n'
        ' else function ng { ng "$@"; }\n'
        "fi\n"
        "ng edu.harvard.hul.ois.fits.Fits"
        ' -i "%relativeLocation%"'
        ' -o "$tempdir/fits.xml" >/dev/null\n'
        'cat "$tempdir/fits.xml"\n'
        'rm -r "$tempdir"'
    )

    FPCommand.objects.create(
        uuid=NEW_FITS_CMD_UUID,
        tool_id=fits_tool_uuid,
        replaces_id=OLD_FITS_CMD_UUID,
        command_usage="characterization",
        command=new_cmd,
        script_type="bashScript",
        output_format_id=xml_format_uuid,
        description="FITS",
    )

    FPRule.objects.filter(uuid=OLD_FITS_RULE_UUID).update(enabled=False)

    FPRule.objects.create(
        uuid=NEW_FITS_RULE_UUID,
        replaces_id=OLD_FITS_RULE_UUID,
        format_id=unknown_format_uuid,
        command_id=NEW_FITS_CMD_UUID,
        purpose="default_characterization",
    )


def data_mgiration_down(apps, schema_editor):
    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    FPRule.objects.filter(uuid=NEW_FITS_RULE_UUID).delete()
    FPRule.objects.filter(uuid=OLD_FITS_RULE_UUID).update(enabled=True)
    FPCommand.objects.filter(uuid=NEW_FITS_CMD_UUID).delete()
    FPCommand.objects.filter(uuid=OLD_FITS_CMD_UUID).update(enabled=True)


class Migration(migrations.Migration):

    dependencies = [("fpr", "0025_update_fido_1312")]

    operations = [migrations.RunPython(data_migration_up, data_mgiration_down)]
