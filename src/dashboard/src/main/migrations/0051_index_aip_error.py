# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def data_migration_up(apps, schema_editor):
    """Workflow migration making Index AIP continue even when it fails.

    Before this change, Index AIP used to fall back to "Email fail report"
    which interrupted the process.
    """

    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')

    clean_up_after_storing_aip_pk = 'b7cf0d9a-504f-4f4e-9930-befa817d67ff'
    MicroServiceChainLink.objects.filter(
        pk='48703fad-dc44-4c8e-8f47-933df3ef6179'
    ).update(
        defaultnextchainlink_id=clean_up_after_storing_aip_pk,
    )


def data_migration_down(apps, schema_editor):
    """Unapply migration."""

    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')

    email_fail_report_pk = '7d728c39-395f-4892-8193-92f086c0546f'
    MicroServiceChainLink.objects.filter(
        pk='48703fad-dc44-4c8e-8f47-933df3ef6179'
    ).update(
        defaultnextchainlink_id=email_fail_report_pk,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0050_fix_upload_qubit_setting'),
    ]

    operations = [
        migrations.RunPython(
            data_migration_up,
            data_migration_down),
    ]
