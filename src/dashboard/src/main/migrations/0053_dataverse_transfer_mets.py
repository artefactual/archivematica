# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):

    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    TaskConfig = apps.get_model("main", "TaskConfig")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")


    """
        `StandardTasksConfigs'
    `pk`, '7c17bd71-9683-4598-8662-89ac7e0797b6'
    'execute', 'dataverse_v0.0'
    `arguments`, '\"%SIPDirectory%\"'
    `requiresOutputLock`, 0
    """

    # new standard task
    dv_transfer_mets_task_config_pk = "7c17bd71-9683-4598-8662-89ac7e0797b6"
    StandardTaskConfig.objects.create(
        id=dv_transfer_mets_task_config_pk,
        requires_output_lock=0,
        execute="dataverse_v0.0",
        arguments="%SIPDirectory%",
    )

    """
    `TasksConfigs`
    `pk`, '1a6b8183-d988-47cb-af23-48cf5dd71cb9'
    `taskTypePKReference`, '7c17bd71-9683-4598-8662-89ac7e0797b6'
    `description`, 'Convert Dataverse Structure'
    `taskType`, '36b2e239-4a57-4aa5-8ebc-7a29139baca6'
    """

    conv_dataverse_task = "1a6b8183-d988-47cb-af23-48cf5dd71cb9"
    task_type_one_instance = "36b2e239-4a57-4aa5-8ebc-7a29139baca6"

    TaskConfig.objects.create(
        id=conv_dataverse_task,
        tasktype_id=task_type_one_instance,
        tasktypepkreference=dv_transfer_mets_task_config_pk,
        description="Convert Dataverse Structure",
    )

    """
    `MicroServiceChainLinks`
    `pk`, '3e02f395-a030-47a5-b9fb-a32eb46144bc'
    `microserviceGroup`, 'Verify transfer compliance'
    `reloadFileList`, 1
    `defaultExitMessage`, 4
    `currentTask`, '1a6b8183-d988-47cb-af23-48cf5dd71cb9'
    `defaultNextChainLink`, '61c316a6-0a50-4f65-8767-1f44b1eeb6dd'
    """


    conv_dataverse_chainlink = "3e02f395-a030-47a5-b9fb-a32eb46144bc"
    fail_transfer = "61c316a6-0a50-4f65-8767-1f44b1eeb6dd"

    MicroServiceChainLink.objects.create(
        id=conv_dataverse_chainlink,
        microservicegroup="Verify transfer compliance",
        defaultexitmessage="Failed",
        currenttask_id=conv_dataverse_task,
        defaultnextchainlink_id=fail_transfer,
    )

    """
    `MicroServiceChainLinksExitCodes`
    `pk`, 'b4760b68-d9d9-4e63-ac50-85caa09eeaaf'
    `exitCode`, 0
    `exitMessage`, 2
    `microServiceChainLink`, '3e02f395-a030-47a5-b9fb-a32eb46144bc'
    `nextMicroServiceChainLink`, '7d0616b2-afed-41a6-819a-495032e86291'
    """

    attempt_restructure_for_compliance = "ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c"
    completed_successfully_code = 2

    MicroServiceChainLinkExitCode.objects.create(
        id="b4760b68-d9d9-4e63-ac50-85caa09eeaaf",
        microservicechainlink_id=conv_dataverse_chainlink,
        exitcode=0,
        nextmicroservicechainlink_id=attempt_restructure_for_compliance,
        exitmessage=completed_successfully_code,
    )

    remove_unneeded_files = "5d780c7d-39d0-4f4a-922b-9d1b0d217bca"

    # Update default chainlink for remove_unneeded_files
    MicroServiceChainLink.objects.filter(
        id=remove_unneeded_files
    ).update(defaultnextchainlink_id=conv_dataverse_chainlink)

    """
    `MicroServiceChainLinksExitCodes`
    SET `nextMicroServiceChainLink`='3e02f395-a030-47a5-b9fb-a32eb46144bc'
    WHERE `pk`='9cb81a5c-a7a1-43a8-8eb6-3e999923e03c';
    """

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id=remove_unneeded_files
    ).update(nextmicroservicechainlink_id=conv_dataverse_chainlink)


class Migration(migrations.Migration):
    dependencies = [("main", "0052_dataverse_poc")]
    operations = [migrations.RunPython(data_migration)]
