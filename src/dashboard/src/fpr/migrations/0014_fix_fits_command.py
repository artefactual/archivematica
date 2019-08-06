# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Fix the FITS characterization FPR command. Disable the old FITS
    command/rule, create a new FITS command that does not pollute the
    command output, i.e., render it invalid XML, disable the existing default
    characterization via FITS rule, and finally create a new default
    characterization rule that uses the new FITS command. See
    https://github.com/artefactual/archivematica-fpr-tools/pull/5
    """

    FPCommand = apps.get_model("fpr", "FPCommand")
    FPRule = apps.get_model("fpr", "FPRule")

    old_fits_cmd_uuid = "183f6d5f-3a8e-4e5a-a6bc-948b9bfca176"
    new_fits_cmd_uuid = "0b0d301f-b586-45d5-ba35-d76da57ce32a"
    old_fits_rule_uuid = "0eee2e2a-a31e-4b3e-a179-ef7211020c3b"
    new_fits_rule_uuid = "296a131d-ce70-45ae-b800-6c71b3ea46f0"
    fits_tool_uuid = "c5465b07-8dc7-475e-a5c9-ccb2ba2ed083"
    xml_format_uuid = "d60e5243-692e-4af7-90cd-40c53cb8dc7d"
    unknown_format_uuid = "0ab4cd40-90e7-4d75-b294-498177b3897d"

    FPCommand.objects.filter(uuid=old_fits_cmd_uuid).update(enabled=False)

    new_cmd = (
        "set -euo pipefail\n"
        "IFS=$'\\n\\t'\n"
        "tempdir=$(mktemp -d %tmpDirectory%fits.XXXXXX)\n"
        "ng edu.harvard.hul.ois.fits.Fits"
        ' -i "%relativeLocation%"'
        ' -o "$tempdir/fits.xml" >/dev/null\n'
        'cat "$tempdir/fits.xml"\n'
        'rm -r "$tempdir"'
    )

    FPCommand.objects.create(
        uuid=new_fits_cmd_uuid,
        tool_id=fits_tool_uuid,
        replaces_id=old_fits_cmd_uuid,
        command_usage="characterization",
        command=new_cmd,
        script_type="bashScript",
        output_format_id=xml_format_uuid,
        description="FITS",
    )

    FPRule.objects.filter(uuid=old_fits_rule_uuid).update(enabled=False)

    FPRule.objects.create(
        uuid=new_fits_rule_uuid,
        replaces_id=old_fits_rule_uuid,
        format_id=unknown_format_uuid,
        command_id=new_fits_cmd_uuid,
        purpose="default_characterization",
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0013_normalization_rules_mov")]

    operations = [migrations.RunPython(data_migration)]
