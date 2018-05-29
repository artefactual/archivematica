# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

from django.db import models, migrations


def data_migration(apps, schema_editor):
    JobFailMessage = apps.get_model('main', 'JobFailMessage')

    Message = namedtuple('Message', 'link_id message')
    job_fail_messages = (
        Message(
            link_id='b4567e89-9fea-4256-99f5-a88987026488',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='0e1a8a6b-abcc-4ed6-b4fb-cbccfdc23ef5',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='aa9ba088-0b1e-4962-a9d7-79d7a0cbea2d',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='45063ad6-f374-4215-a2c4-ac47be4ce2cd',
            message='The Transfer must fixed to meet the definition of the '
                    'Transfer Type to proceed, or you can reject the Transfer '
                    'and start again. User input is required in the dashboard '
                    'to select the appropriate option. Select "reject" to '
                    'delete the transfer, select "attempt restructure for '
                    'compliance" to have Archivematica attempt to fix the '
                    'problem, or modify the Transfer contents within the '
                    'Currently Processing directory and select '
                    '"move to ActiveTransfers" to restart processing.',
        ),
        Message(
            link_id='438dc1cf-9813-44b5-a0a3-58e09ae73b8a',
            message='The Transfer must fixed to meet the definition of the '
                    'Transfer Type to proceed, or you can reject the Transfer '
                    'and start again. User input is required in the dashboard '
                    'to select the appropriate option. Select "reject" to '
                    'delete the transfer, select "attempt restructure for '
                    'compliance" to have Archivematica attempt to fix the '
                    'problem, or modify the Transfer contents within the '
                    'Currently Processing directory and select "move to '
                    'ActiveTransfers" to restart processing.',
        ),
        Message(
            link_id='5e4bd4e8-d158-4c2a-be89-51e3e9bd4a06',
            message='At least one checksum provided in the Transfer is not '
                    'accurate for the file it is meant to describe. This '
                    'could be due to a problem in the checksum file, or may '
                    'be because the file itself has been corrupted or '
                    'modified since the original checksum was created. Check '
                    'the dashboard for this job to see a list of standard '
                    'errors for each file that had a checksum that did not '
                    'pass verification.'
        ),
        Message(
            link_id='7c6a0b72-f37b-4512-87f3-267644de6f80',
            message='At least one checksum provided in the Transfer is not '
                    'accurate for the file it is meant to describe. This '
                    'could be due to a problem in the checksum file, or may '
                    'be because the file itself has been corrupted or '
                    'modified since the original checksum was created. Check '
                    'the dashboard for this job to see a list of standard '
                    'errors for each file that had a checksum that did not '
                    'pass verification.'
        ),
        Message(
            link_id='f1bfce12-b637-443f-85f8-b6450ca01a13',
            message='At least one checksum provided in the Transfer is not '
                    'accurate for the file it is meant to describe. This '
                    'could be due to a problem in the checksum file, or may '
                    'be because the file itself has been corrupted or '
                    'modified since the original checksum was created. Check '
                    'the dashboard for this job to see a list of standard '
                    'errors for each file that had a checksum that did not '
                    'pass verification.'
        ),
        Message(
            link_id='1c2550f1-3fc0-45d8-8bc4-4c06d720283b',
            message='Check the Dashboard to see which files contain viruses. '
                    'Remove infected files and start the Transfer process '
                    'over again.',
        ),
        Message(
            link_id='21d6d597-b876-4b3f-ab85-f97356f10507',
            message='Check the Dashboard to see which files contain viruses. '
                    'Remove infected files and start the Transfer process '
                    'over again.',
        ),
        Message(
            link_id='2522d680-c7d9-4d06-8b11-a28d8bd8a71f',
            message='Format identification will fail if any objects can\'t be '
                    'identified. Consider processing the files again with a '
                    'different tool.',
        ),
        Message(
            link_id='7d33f228-0fa8-4f4c-a66b-24f8e264c214',
            message='Check the Dashboard to see which files contain viruses. '
                    'Remove infected files and start the Transfer process '
                    'over again.',
        ),
        Message(
            link_id='aaa929e4-5c35-447e-816a-033a66b9b90b',
            message='Format identification will fail if any objects can\'t be '
                    'identified. Consider processing the files again with a '
                    'different tool',
        ),
        Message(
            link_id='48703fad-dc44-4c8e-8f47-933df3ef6179',
            message='When "Index AIP" fails, it is not possible to search for '
                    'your AIP through the Archivematica Dashboard. You can '
                    'find the AIP by logging into the Archivematica storage '
                    'service and browsing or searching from the Packages '
                    'screen.',
        ),
        Message(
            link_id='2fd123ea-196f-4c9c-95c0-117aa65ed9c6',
            message='At least one checksum provided in the Transfer is not '
                    'accurate for the file it is meant to describe. This could '
                    'be due to a problem in the checksum file, or may be '
                    'because the file itself has been corrupted or modified '
                    'since the original checksum was created. Check the '
                    'dashboard for this job to see a list of standard errors '
                    'for each file that had a checksum that did not pass '
                    'verification.',
        ),
        Message(
            link_id='888a5bdc-9928-44f0-9fb7-91bc5f1e155b',
            message='At least one checksum provided in the Transfer is not '
                    'accurate for the file it is meant to describe. This could '
                    'be due to a problem in the checksum file, or may be '
                    'because the file itself has been corrupted or modified '
                    'since the original checksum was created. Check the '
                    'dashboard for this job to see a list of standard errors '
                    'for each file that had a checksum that did not pass '
                    'verification.',
        ),
        Message(
            link_id='88807d68-062e-4d1a-a2d5-2d198c88d8ca',
            message='At least one checksum provided in the Transfer is not '
                    'accurate for the file it is meant to describe. This could '
                    'be due to a problem in the checksum file, or may be '
                    'because the file itself has been corrupted or modified '
                    'since the original checksum was created. Check the '
                    'dashboard for this job to see a list of standard errors '
                    'for each file that had a checksum that did not pass '
                    'verification.',
        ),
        Message(
            link_id='303a65f6-a16f-4a06-807b-cb3425a30201',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='bd382151-afd0-41bf-bb7a-b39aef728a32',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='100a75f4-9d2a-41bf-8dd0-aec811ae1077',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='bcabd5e2-c93e-4aaa-af6a-9a74d54e8bf0',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='ef8bd3f3-22f5-4283-bfd6-d458a2d18f22',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='440ef381-8fe8-4b6e-9198-270ee5653454',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='8ce378a5-1418-4184-bf02-328a06e1d3be',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='5c0d8661-1c49-4023-8a67-4991365d70fb',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='e950cd98-574b-4e57-9ef8-c2231e1ce451',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='04493ab2-6cad-400d-8832-06941f121a96',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='33d7ac55-291c-43ae-bb42-f599ef428325',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='a536828c-be65-4088-80bd-eb511a0a063d',
            message='Check the Dashboard to see which files have errors '
                    'associated with them. Some errors may be due to '
                    'limitations of the tools being used. Modifying FPR rules '
                    'to change which tools run on which formats may reduce the '
                    'number of errors produced.',
        ),
        Message(
            link_id='1cb7e228-6e94-4c93-bf70-430af99b9264',
            message='Check the Dashboard to see which files resulted in errors '
                    'during extraction. Some errors may be due to limitations '
                    'of the tools being used. Modifying FPR rules to change '
                    'which tools run on which formats may reduce the number of '
                    'errors produced.',
        ),
        Message(
            link_id='95616c10-a79f-48ca-a352-234cc91eaf08',
            message='Check the Dashboard to see which files resulted in errors '
                    'during extraction. Some errors may be due to limitations '
                    'of the tools being used. Modifying FPR rules to change '
                    'which tools run on which formats may reduce the number of '
                    'errors produced.',
        ),
        Message(
            link_id='61c316a6-0a50-4f65-8767-1f44b1eeb6dd',
            message='Email notifications may fail if a working email server is '
                    'not configured or available. Failure reports can also be '
                    'found through the dashboard.',
        ),
        Message(
            link_id='7d728c39-395f-4892-8193-92f086c0546f',
            message='Email notifications may fail if a working email server is '
                    'not configured or available. Failure reports can also be '
                    'found through the dashboard.',
        ),
        Message(
            link_id='54b73077-a062-41cc-882c-4df1eba447d9',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='ab69c494-23b7-4f50-acff-2e00cf7bffda',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='01fd7a29-deb9-4dd1-8e28-1c48fc1ac41b',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='0e06d968-4b5b-4084-aab4-053a2a8d1679',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='0e379b19-771e-4d90-a7e5-1583e4893c56',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='288b739d-40a1-4454-971b-812127a5e03d',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='5cf308fd-a6dc-4033-bda1-61689bb55ce2',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='8f639582-8881-4a8b-8574-d2f86dc4db3d',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='d3c75c96-f8c7-4674-af46-5bcce7b05f87',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='d7e6404a-a186-4806-a130-7e6d27179a15',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='f7488721-c936-42af-a767-2f0b39564a86',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='f8be53cd-6ca2-4770-8619-8a8101a809b9',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='3e75f0fa-2a2b-4813-ba1a-b16b4be4cac5',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='d27fd07e-d3ed-4767-96a5-44a2251c6d0a',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='abd6d60c-d50f-4660-a189-ac1b34fafe85',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='dae3c416-a8c2-4515-9081-6dbd7b265388',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='cc16178b-b632-4624-9091-822dd802a2c6',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='377f8ebb-7989-4a68-9361-658079ff8138',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='559d9b14-05bf-4136-918a-de74a821b759',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='6eca2676-b4ed-48d9-adb0-374e1d5c6e71',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='d1b27e9e-73c8-4954-832c-36bd1e00c802',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='c2e6600d-cd26-42ed-bed5-95d41c06e37b',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='0f0c1f33-29f2-49ae-b413-3e043da5df61',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='424ee8f1-6cdd-4960-8641-ed82361d3ad7',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='5f213529-ced4-49b0-9e30-be4e0c9b81d5',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='6327fdf9-9673-42a8-ace5-cccad005818b',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='6b39088b-683e-48bd-ab89-9dab47f4e9e0',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='70669a5b-01e4-4ea0-ac70-10292f87da05',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='70f41678-baa5-46e6-a71c-4b6b4d99f4a6',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='b20ff203-1472-40db-b879-0e59d17de867',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='c103b2fb-9a6b-4b68-8112-b70597a6cd14',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='cddde867-4cf9-4248-ac31-f7052fae053f',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='efd15406-fd6c-425b-8772-d460e1e79009',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='a2173b55-abff-4d8f-97b9-79cc2e0a64fa',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='0c2c9c9a-25b2-4a2d-a790-103da79f9604',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='88d2120a-4d19-4b47-922f-7438be1f52a2',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='ee438694-815f-4b74-97e1-8e7dde2cc6d5',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='e4b0c713-988a-4606-82ea-4b565936d9a7',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='173d310c-8e40-4669-9a69-6d4c8ffd0396',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='2adf60a0-ecd7-441a-b82f-f77c6a3964c3',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='67a91b4b-a5af-4b54-a836-705e6cf4eeb9',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='03ee1136-f6ad-4184-8dcb-34872f843e14',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='7d0616b2-afed-41a6-819a-495032e86291',
            message='Failure to move or copy files may be due to lack of disk '
                    'space. Check Processing Storage Usage in the '
                    'Administration screen, or contact your administrator.',
        ),
        Message(
            link_id='2dd53959-8106-457d-a385-fee57fc93aa9',
            message='Format identification will fail if any objects can\'t be '
                    'identified. Consider processing the files again with a '
                    'different tool.',
        ),
        Message(
            link_id='0e41c244-6c3e-46b9-a554-65e66e5c9324',
            message='Format identification will fail if any objects can\'t be '
                    'identified. Consider processing the files again with a '
                    'different tool.',
        ),
        Message(
            link_id='22ded604-6cc0-444b-b320-f96afb15d581',
            message='Format identification will fail if any objects can\'t be '
                    'identified. Consider processing the files again with a '
                    'different tool.',
        ),
        Message(
            link_id='b2444a6e-c626-4487-9abc-1556dd89a8ae',
            message='Format identification will fail if any objects can\'t be '
                    'identified. Consider processing the files again with a '
                    'different tool.',
        ),
        Message(
            link_id='1dce8e21-7263-4cc4-aa59-968d9793b5f2',
            message='Format identification will fail if any objects can\'t be '
                    'identified. Consider processing the files again with a '
                    'different tool.',
        ),
    )
    for item in job_fail_messages:
        JobFailMessage.objects.create(
            microservicechainlink_id=item.link_id,
            message=item.message,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0051_index_aip_error'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobFailMessage',
            fields=[
                ('id', models.AutoField(
                    serialize=False, editable=False,
                    primary_key=True, db_column=b'pk')),
                ('microservicechainlink', models.ForeignKey(
                    to='main.MicroServiceChainLink',
                    db_column=b'microServiceChainLinksPK')),
                ('message', models.CharField(
                    max_length=1000,
                    db_column=b'message')),
                ('lastmodified', models.DateTimeField(
                    db_column=b'lastModified', auto_now=True)),
            ],
            options={
                'db_table': 'JobFailMessages',
            },
            bases=(models.Model,),
        ),

        migrations.RunPython(data_migration)
    ]
