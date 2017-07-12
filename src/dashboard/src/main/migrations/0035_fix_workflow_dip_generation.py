# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def data_migration(apps, schema_editor):
    """Migrations to fix the workflow so that the "Check if DIP should be
    generated" link is reachable. The previous migration inadvertently orphaned
    this link.
    """
    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')
    MicroServiceChainLinkExitCode = apps.get_model(
        'main', 'MicroServiceChainLinkExitCode')
    add_readme_file_cl_uuid = '523c97cc-b267-4cfb-8209-d99e523bf4b3'
    check_if_dip_gen_cl_uuid = 'f1e286f9-4ec7-4e19-820c-dae7b8ea7d09'
    # "Add README file" -> "Check if DIP should be generated"
    MicroServiceChainLinkExitCode.objects\
        .filter(microservicechainlink_id=add_readme_file_cl_uuid)\
        .update(nextmicroservicechainlink_id=check_if_dip_gen_cl_uuid)
    MicroServiceChainLink.objects\
        .filter(id=add_readme_file_cl_uuid)\
        .update(defaultnextchainlink=check_if_dip_gen_cl_uuid)


class Migration(migrations.Migration):

    dependencies = [('main', '0034_add_readme_to_aips')]
    operations = [
        migrations.RunPython(data_migration),
        # Also modify File.modificationtime so that it corresponds to the
        # camelCased database column name.
        migrations.AlterField(
            model_name='file',
            name='modificationtime',
            field=models.DateTimeField(auto_now_add=True,
                                       db_column=b'modificationTime'))
    ]
