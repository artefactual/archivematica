# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def data_migration_put_quotes_in_compress_aip_args(apps, schema_editor):
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')

    tasks = (
        # upload-archivesspace.py
        (
            '10a0f352-aeb7-4c13-8e9e-e81bda9bca29',
            u'--host="%host%" --port="%port%" --user="%user%"'
            u' --passwd="%passwd%" --dip_location="%SIPDirectory%"'
            u' --dip_name="%SIPName%" --dip_uuid="%SIPUUID%"'
            u' --restrictions="%restrictions%" --object_type="%object_type%"'
            u' --xlink_actuate="%xlink_actuate%" --xlink_show="%xlink_show%"'
            u' --use_statement "%use_statement%" --uri_prefix "%uri_prefix%"'
            u' --access_conditions "%access_conditions%"'
            u' --use_conditions="%use_conditions%"'
            u' --inherit_notes="%inherit_notes%"'
        ),
        # storeAIP.py
        (
            '1e4ccd56-a076-4aa2-9642-1ed8944b306a',
            u'-- "%DIPsStore%"'
            u' "%watchDirectoryPath%uploadedDIPs/%SIPName%-%SIPUUID%"'
            u' "%SIPUUID%" "%SIPName%" "DIP"'
        ),
        (
            '1f6f0cd1-acaf-40fb-bb2a-047383b8c977',
            u'-- "%DIPsStore%"'
            u' "%watchDirectoryPath%uploadDIP/%SIPName%-%SIPUUID%"'
            u' "%SIPUUID%" "%SIPName%" "DIP"'
        ),
        (
            '7df9e91b-282f-457f-b91a-ad6135f4337d',
            u'-- "%AIPsStore%" "%SIPDirectory%%AIPFilename%" "%SIPUUID%"'
            u' "%SIPName%" "%SIPType%"'
        ),
        # compressAIP.py
        (
            '4dc2b1d2-acbb-47e7-88ca-570281f3236f',
            u'-- %AIPCompressionAlgorithm% %AIPCompressionLevel%'
            u' %SIPDirectory% "%SIPName%" %SIPUUID%'
        ),
        # emailFailReport.py
        (
            '807603e2-9914-46e0-9be4-73d4c073d2e8',
            u'--unitType="%unitType%"'
            u' --unitIdentifier="%SIPUUID%" --unitName="%SIPName%"'
        ),
    )

    for stc, args in tasks:
        task = StandardTaskConfig.objects.get(id=stc)
        task.arguments = args
        task.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0052_correct_extract_packages_fallback_link'),
    ]

    operations = [
        migrations.RunPython(data_migration_put_quotes_in_compress_aip_args),
    ]
