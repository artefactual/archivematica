# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def data_migration(apps, schema_editor):
    JobFailMessage = apps.get_model('main', 'JobFailMessage')

    # Verify Transfer Compliance    Move to processing directory
    JobFailMessage.objects.create(
        microservicechainlink_id=u'b4567e89-9fea-4256-99f5-a88987026488',
        message='''Failure to move or copy files may be due to lack of disk space.
         Check Processing Storage Usage in the Administration screen, or contact your administrator.''',
    )
    JobFailMessage.objects.create(
        microservicechainlink_id=u'0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5',
        message='''Failure to move or copy files may be due to lack of disk space.
         Check Processing Storage Usage in the Administration screen, or contact your administrator.''',
    )
    JobFailMessage.objects.create(
        microservicechainlink_id=u'aa9ba088-0b1e-4962-a9d7-79d7a0cbea2d',
        message=("Failure to move or copy files may be due to lack of disk space. "
                 "Check Processing Storage Usage in the Administration screen, or contact your administrator."),
    )
    # Verify Transfer Compliance  Attempt restructure for compliance
    JobFailMessage.objects.create(
        microservicechainlink_id=u'ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c',
        message=("Failure to move or copy files may be due to lack of disk space. "
                 "Check Processing Storage Usage in the Administration screen, or contact your administrator."),
    )
    # Verify Transfer Compliance  Verify Transfer Compliance
    JobFailMessage.objects.create(
        microservicechainlink_id=u'45063ad6-f374-4215-a2c4-ac47be4ce2cd',
        message=("The Transfer must fixed to meet the definition of the Transfer Type to proceed, or you can reject "
                 "the Transfer and start again. User input is required in the dashboard to select the appropriate option. "
                 "Select \"reject\" to delete the transfer, select \"attempt restructure for compliance\" to have "
                 "Archivematica attempt to fix the problem, or modify the Transfer contents within the "
                 "Currently Processing directory and select \"move to ActiveTransfers\" to restart processing. "),
    )
    JobFailMessage.objects.create(
        microservicechainlink_id=u'438dc1cf-9813-44b5-a0a3-58e09ae73b8a',
        message=("The Transfer must fixed to meet the definition of the Transfer Type to proceed, or you can reject "
                 "the Transfer and start again. User input is required in the dashboard to select the appropriate option. "
                 "Select \"reject\" to delete the transfer, select \"attempt restructure for compliance\" to have "
                 "Archivematica attempt to fix the problem, or modify the Transfer contents within the "
                 "Currently Processing directory and select \"move to ActiveTransfers\" to restart processing. "),
    )
    # Verify transfer checksums    Verify metadata directory checksums
    JobFailMessage.objects.create(
        microservicechainlink_id=u'5e4bd4e8-d158-4c2a-be89-51e3e9bd4a06',
        message=("At least one checksum provided in the Transfer is not accurate for the file "
                 "it is meant to describe. This could be due to a problem in the checksum file, "
                 "or may be because the file itself has been corrupted or modified since the original "
                 "checksum was created. Check the dashboard for this job to see a list of standard errors "
                 "for each file that had a checksum that did not pass verification."),
    )
    JobFailMessage.objects.create(
        microservicechainlink_id=u'7c6a0b72-f37b-4512-87f3-267644de6f80',
        message=("At least one checksum provided in the Transfer is not accurate for the file "
                 "it is meant to describe. This could be due to a problem in the checksum file, "
                 "or may be because the file itself has been corrupted or modified since the original "
                 "checksum was created. Check the dashboard for this job to see a list of standard errors "
                 "for each file that had a checksum that did not pass verification."),
    )
    JobFailMessage.objects.create(
        microservicechainlink_id=u'f1bfce12-b637-443f-85f8-b6450ca01a13',
        message=("At least one checksum provided in the Transfer is not accurate for the file "
                 "it is meant to describe. This could be due to a problem in the checksum file, "
                 "or may be because the file itself has been corrupted or modified since the original "
                 "checksum was created. Check the dashboard for this job to see a list of standard errors "
                 "for each file that had a checksum that did not pass verification."),
    )
    # Scan for viruses  Scan for viruses
    JobFailMessage.objects.create(
        microservicechainlink_id=u'1c2550f1-3fc0-45d8-8bc4-4c06d720283b',
        message=("Check the Dashboard to see which files contain viruses. "
                 "Remove infected files and start the Transfer process over again. "),
    )
    JobFailMessage.objects.create(
        microservicechainlink_id=u'21d6d597-b876-4b3f-ab85-f97356f10507',
        message=("Check the Dashboard to see which files contain viruses. "
                 "Remove infected files and start the Transfer process over again. "),
    )
    # Identify File Format  Identify File Format
    JobFailMessage.objects.create(
        microservicechainlink_id=u'2522d680-c7d9-4d06-8b11-a28d8bd8a71f',
        message=("Format identification will fail if any objects can't be identified. "
                 "Consider processing the files again with a different tool."),
    )
    # Extract packages  Scan for viruses on extracted files
    JobFailMessage.objects.create(
        microservicechainlink_id=u'7d33f228-0fa8-4f4c-a66b-24f8e264c214',
        message=("Check the Dashboard to see which files contain viruses. "
                 "Remove infected files and start the Transfer process over again. "),
    )
    # Extract packages  Identifies formats of the objects in the transfer.
    JobFailMessage.objects.create(
        microservicechainlink_id=u'aaa929e4-5c35-447e-816a-033a66b9b90b',
        message=("Format identification will fail if any objects can't be identified. "
                 "Consider processing the files again with a different tool."),
    )
    # Store AIP  Index AIP
    JobFailMessage.objects.create(
        microservicechainlink_id=u'48703fad-dc44-4c8e-8f47-933df3ef6179',
        message=("When 'Index AIP' fails, it is not possible to search for your AIP "
                 "through the Archivematica Dashboard. You can find the AIP by logging "
                 "into the Archivematica storage service and browsing or searching from the Packages screen."),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0051_index_aip_error'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobFailMessage',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('microservicechainlink', models.ForeignKey(to='main.MicroServiceChainLink', db_column=b'microServiceChainLinksPK')),
                ('message', models.CharField(max_length=1000, db_column=b'message')),
                ('lastmodified', models.DateTimeField(db_column=b'lastModified', auto_now=True)),
            ],
            options={
                'db_table': 'JobFailMessages',
            },
            bases=(models.Model,),
        ),

        migrations.RunPython(data_migration)
    ]
