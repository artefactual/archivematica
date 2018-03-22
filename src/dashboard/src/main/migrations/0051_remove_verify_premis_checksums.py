# -*- coding: utf-8 -*-

"""Migration to remove the "Verify checksums generated on ingest" (Ingest)
micro-service which is redundant. See
https://github.com/artefactual/archivematica/issues/918.
"""

from __future__ import unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Remove the "Verify checksums generated on ingest" micro-service. This is
    verifyPREMISChecksums_v0.0 or verifyPREMISChecksums.py.
    """

    ###########################################################################
    # Model classes
    ###########################################################################

    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')
    TaskConfig = apps.get_model('main', 'TaskConfig')
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')
    MicroServiceChainLinkExitCode = apps.get_model(
        'main', 'MicroServiceChainLinkExitCode')

    ###########################################################################
    # "Remove empty manual normalization directories" now continues on to
    # "Bind PIDs?"
    ###########################################################################

    MicroServiceChainLink.objects.filter(
        id='75fb5d67-5efa-4232-b00b-d85236de0d3f'
    ).update(
        defaultnextchainlink_id='05357876-a095-4c11-86b5-a7fff01af668')
    MicroServiceChainLinkExitCode.objects.filter(
        nextmicroservicechainlink='88807d68-062e-4d1a-a2d5-2d198c88d8ca'
    ).update(
        nextmicroservicechainlink='05357876-a095-4c11-86b5-a7fff01af668')

    ###########################################################################
    # Remove "Verify checksums generated on ingest"
    ###########################################################################

    StandardTaskConfig.objects.get(
        id='4f400b71-37be-49d0-8da3-125abac2bfd0').delete()
    TaskConfig.objects.get(
        id='ef024cf9-1737-4161-b48a-13b4a8abddcd').delete()

    # The above will result in the following:
    # MicroServiceChainLink.objects.get(
    #     id='88807d68-062e-4d1a-a2d5-2d198c88d8ca').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0050_change_pointer_file_filegrpuse'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]
