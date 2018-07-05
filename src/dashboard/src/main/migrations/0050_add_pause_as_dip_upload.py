# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Workflow migrations to add a pause in ArchivesSpace DIP Upload
          Address issue #1112 - WORK IN PROGRESS
    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    TaskType = apps.get_model('main', 'TaskType')
    TaskConfig = apps.get_model('main', 'TaskConfig')
    MicroServiceChain = apps.get_model('main', 'MicroServiceChain')
    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')
    MicroServiceChainLinkExitCode = apps.get_model(
        'main', 'MicroServiceChainLinkExitCode')
    MicroServiceChainChoice = apps.get_model('main', 'MicroServiceChainChoice')

    ###########################################################################
    # Get Existing Model Instances
    ###########################################################################

    user_choice_type = TaskType.objects.get(
        description='get user choice to proceed with')

    ###########################################################################
    # BEGIN Micro-service that asks "Continue DIP Upload to ArchivesSpace?
    ###########################################################################

    # get the uuid's for the chain links that should be after this new choice
    # i.e. the  "Upload to ArchivesSpace" chain link.
    upload_as_cl = MicroServiceChainLink.objects.filter(
        currenttask__description='Upload to ArchivesSpace').first()
    upload_as_cl_ttpkr = upload_as_cl.currenttask.tasktypepkreference

    # Continue DIP Upload CHOICE POINT Task Config
    continue_dip_upload_choice_tc_pk = '86995583-4369-48d0-a7c6-613f77aaf4fe'
    continue_dip_upload_choice_tc = TaskConfig.objects.create(
        id=continue_dip_upload_choice_tc_pk,
        tasktype=user_choice_type,
        tasktypepkreference=upload_as_cl_ttpkr,
        description='Continue DIP Upload to ArchivesSpace?'
    )

    # "Continue DIP Upload to ArchivesSpace?" CHOICE chain link.
    continue_dip_upload_check_choice_cl_pk = \
        'b4cb177f-5573-4897-a489-e8f4f0a21346'
    continue_dip_upload_check_choice_cl = MicroServiceChainLink.objects.create(
        id=continue_dip_upload_check_choice_cl_pk,
        currenttask=continue_dip_upload_choice_tc,
        defaultnextchainlink=None,
        microservicegroup='Upload DIP'
    )

    # Insert this new question between Choose config and upload to archivesspace'
    MicroServiceChainLinkExitCode.objects\
        .filter(nextmicroservicechainlink=upload_as_cl)\
        .update(nextmicroservicechainlink=continue_dip_upload_check_choice_cl)
    MicroServiceChainLink.objects\
        .filter(defaultnextchainlink=upload_as_cl)\
        .exclude(id=continue_dip_upload_check_choice_cl_pk)\
        .update(defaultnextchainlink=continue_dip_upload_check_choice_cl)

    # MS Chain Choice and Chain that say "Yes, I do want to continue DIP upload'
    chain_yes_msc_pk = \
        '07df9a92-082a-4c6e-8278-f42f71f53a70'
    chain_yes_msc = MicroServiceChain.objects.create(
        id=chain_yes_msc_pk,
        startinglink=upload_as_cl,
        description='Yes'  # Yes, upload my DIP!'
    )

    choice_yes_mscc_pk = \
        '8a579b46-2bd5-4390-aa6f-5673a237b3c1'
    MicroServiceChainChoice.objects.create(
        id=choice_yes_mscc_pk,
        chainavailable=chain_yes_msc,
        choiceavailableatlink=continue_dip_upload_check_choice_cl
    )


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0049_change_pointer_file_filegrpuse'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]
