# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    arguments = " ".join(
        [
            '--host "%host%"',
            '--port "%port%"',
            '--user "%user%"',
            '--passwd "%passwd%"',
            '--dip_location "%SIPDirectory%"',
            '--dip_name "%SIPName%"',
            '--dip_uuid "%SIPUUID%"',
            '--restrictions "%restrictions%"',
            '--object_type "%object_type%"',
            '--xlink_actuate "%xlink_actuate%"',
            '--xlink_show "%xlink_show%"',
            '--use_statement "%use_statement%"',
            '--uri_prefix "%uri_prefix%"',
            '--access_conditions "%access_conditions%"',
            '--use_conditions "%use_conditions%"',
            '--inherit_notes="%inherit_notes%"',
        ]
    )

    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    StandardTaskConfig.objects.filter(pk="10a0f352-aeb7-4c13-8e9e-e81bda9bca29").update(
        arguments=arguments
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0012_file_id_text")]

    operations = [migrations.RunPython(data_migration)]
