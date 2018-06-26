# -*- coding: utf-8 -*-
"""Migration to create a new Dataverse set of chain-links inside Archivematica.
"""
from __future__ import unicode_literals

import logging

from django.db import migrations

# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def undo_create_dataverse_entry_point(apps):
    return


def undo_create_first_microservice_chainlink(apps):
    return


def undo_create_microservice_chain(apps):
    return


def undo_create_watched_directory(apps):
    watched_directory_model = apps.get_model('main', 'WatchedDirectory')
    watched_directory_model.objects\
        .filter(id="3901db52-dd1d-4b44-9d86-4285ddc5c022").delete()


def undo_create_microservice_chain_choice(apps):
    return


def data_migration_down(apps, schema_editor):
    """Reset the two fields in the Dashboard data model for the two affected
    transfer types.
    """
    undo_create_dataverse_entry_point(apps)
    undo_create_first_microservice_chainlink(apps)
    undo_create_watched_directory(apps)


def create_dataverse_entry_point(apps):
    """
    pk, '246943e4-d203-48e1-ac84-4865520e7c30',
    microserviceGroup, 'Approve transfer',
    reloadFileList, '1',
    defaultExitMessage, '4',
    lastModified, '2018-10-02 00:25:06.000000',
    currentTask, '477bc37e-b6a7-440a-9088-85672b3b38a7',
    defaultNextChainLink, NULL
    replaces, NULL
    """
    approve_dataverse_transfer_task_config = apps\
        .get_model('main', 'TaskConfig')\
        .objects.get(id='477bc37e-b6a7-440a-9088-85672b3b38a7')
    logger.info("Retrieved dataverse transfer task config %s",
                approve_dataverse_transfer_task_config)
    chain_link_table = apps.get_model('main', 'MicroServiceChainLink')
    chain_link_table.objects.create(
        id="246943e4-d203-48e1-ac84-4865520e7c30",
        microservicegroup="Approve transfer",
        reloadfilelist=1,
        defaultexitmessage=4,
        currenttask=approve_dataverse_transfer_task_config,
    )


def create_first_microservice_chainlink(apps):
    """
    pk, '477bc37e-b6a7-440a-9088-85672b3b38a7',
    taskTypePKReference, NULL,
    description, 'Approve Dataverse Transfer',
    lastModified, '2018-10-02 00:25:11.000000',
    replaces, NULL,
    taskType, '61fb3874-8ef6-49d3-8a2d-3cb66e86a30c'
    """
    get_user_choice_task_type = apps\
        .get_model('main', 'TaskType')\
        .objects.get(id='61fb3874-8ef6-49d3-8a2d-3cb66e86a30c')
    logger.info("Retrieved user choice task type: %s",
                get_user_choice_task_type)
    tasks_config_table = apps.get_model('main', 'TaskConfig')
    tasks_config_table.objects.create(
        id='477bc37e-b6a7-440a-9088-85672b3b38a7',
        description="Approve Dataverse Transfer",
        tasktype=get_user_choice_task_type,
    )


def create_microservice_chain(apps):
    """
    # pk, '35a26b59-dcf3-45ec-b963-ba7bfaa8304f',
    description, 'Dataverse Transfers in Progress',
    lastModified, '2018-10-02 00:25:08.000000',
    replaces, NULL,
    startingLink, '246943e4-d203-48e1-ac84-4865520e7c30'
    """
    approve_transfer_chain_link = apps\
        .get_model('main', 'MicroServiceChainLink')\
        .objects.get(id='246943e4-d203-48e1-ac84-4865520e7c30')
    logger.info("Retrieved chainlink object: %s", approve_transfer_chain_link)
    microservice_chain_table = apps.get_model("main", "MicroServiceChain")
    microservice_chain_table.objects.create(
        id="35a26b59-dcf3-45ec-b963-ba7bfaa8304f",
        description="Dataverse Transfers in Progress",
        startinglink=approve_transfer_chain_link,
    )


def create_watched_directory(apps):
    transfer_types_table = apps\
        .get_model('main', 'WatchedDirectoryExpectedType')
    transfer_type_uuid = transfer_types_table.objects\
        .filter(description="Transfer").all()[0]
    logger.info("Retrieved transfer type UUID %s", transfer_type_uuid)
    transfers_in_progress_chain = apps\
        .get_model('main', 'MicroServiceChain')\
        .objects.get(id='35a26b59-dcf3-45ec-b963-ba7bfaa8304f')
    watched_directory_path = ("%watchDirectoryPath%activeTransfers/"
                              "dataverseTransfer")
    watched_directory_model = apps.get_model('main', 'WatchedDirectory')
    watched_directory_model.objects.create(
        id="3901db52-dd1d-4b44-9d86-4285ddc5c022",
        watched_directory_path=watched_directory_path,
        only_act_on_directories=1,
        expected_type=transfer_type_uuid,
        chain=transfers_in_progress_chain,
    )


def create_microservice_chain_choice(apps):
    """
    # pk, '77bb4993-9f5b-4e60-bbe9-0039a6f5934e',
    lastModified, '2012-10-02 00:25:05.000000',
    chainAvailable, '6953950b-c101-4f4c-a0c3-0cd0684afe5e',
    choiceAvailableAtLink, '246943e4-d203-48e1-ac84-4865520e7c30',
    replaces, NULL


    # pk, 'dc9b59b3-dd5f-4cd6-8e97-ee1d83734c4c',
    lastModified, '2012-10-02 00:25:05.000000',
    chainAvailable, '1b04ec43-055c-43b7-9543-bd03c6a778ba',
    choiceAvailableAtLink, '246943e4-d203-48e1-ac84-4865520e7c30',
    replaces,  NULL
    """

    microservice_chain_choice_table = apps\
        .get_model('main', 'MicroServiceChainChoice')

    microservice_chain_link_table = apps\
        .get_model("main", "MicroServiceChainLink")
    dataverse_chain = microservice_chain_link_table\
        .objects.filter(id='246943e4-d203-48e1-ac84-4865520e7c30').all()[0]

    microservice_chain_table = apps.get_model("main", "MicroServiceChain")
    approve = microservice_chain_table\
        .objects.filter(id='6953950b-c101-4f4c-a0c3-0cd0684afe5e').all()[0]
    reject = microservice_chain_table\
        .objects.filter(id='1b04ec43-055c-43b7-9543-bd03c6a778ba').all()[0]

    # Create a reject transfer choice
    microservice_chain_choice_table.objects.create(
        id='dc9b59b3-dd5f-4cd6-8e97-ee1d83734c4c',
        chainavailable=approve,
        choiceavailableatlink=dataverse_chain,
    )

    # Create an approve transfer choice...
    microservice_chain_choice_table.objects.create(
        id='77bb4993-9f5b-4e60-bbe9-0039a6f5934e',
        chainavailable=reject,
        choiceavailableatlink=dataverse_chain,
    )


def data_migration_up(apps, schema_editor):
    """Run the various pieces needed to create a Dataverse set of chain-links.
    """

    return

    # 1. we need to create the first chain link so that the first job can
    # begin. This will be an 'Approve Dataverse Transfer' link.
    create_first_microservice_chainlink(apps)

    # 2. we then need to create an entry point in MicroServiceChains, this will
    # be a dataverse transfers in progress Chain that points to the first
    # dataverse micro-service.
    create_dataverse_entry_point(apps)

    # 4. we then need to create a microservice chain from which to begin it
    # all.
    create_microservice_chain(apps)

    # 4. we need to create a watched directory which links back to 1. so that
    # when something is added to the dataverse specific one, it can look up the
    # first chain to begin following.
    create_watched_directory(apps)

    # 5. we need to create an option to accept or reject the transfer, this is
    # done by creating a microservice chain choice.
    create_microservice_chain_choice(apps)


class Migration(migrations.Migration):
    """Entry point for the migration."""
    dependencies = [('main', '0053_dataverse_transfer_mets')]
    operations = [
        migrations.RunPython(data_migration_up, data_migration_down)
    ]
