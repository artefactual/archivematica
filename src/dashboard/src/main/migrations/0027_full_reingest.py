# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    TaskConfig = apps.get_model("main", "TaskConfig")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfigUnitVariableLinkPull = apps.get_model(
        "main", "TaskConfigUnitVariableLinkPull"
    )

    # Add SIPUUID argument to restructureForCompliance_v0.0
    StandardTaskConfig.objects.filter(execute="restructureForCompliance_v0.0").update(
        arguments='"%SIPDirectory%" "%SIPUUID%"'
    )

    # Add sharedPath argument to updateSizeAndChecksum_v0.0
    StandardTaskConfig.objects.filter(execute="updateSizeAndChecksum_v0.0").update(
        arguments='"%sharedPath%" --filePath "%relativeLocation%" --fileUUID "%fileUUID%" --eventIdentifierUUID "%taskUUID%" --date "%date%"'
    )

    # Add failedTransferCleanup script to failed
    StandardTaskConfig.objects.create(
        id="3362ef11-b4f1-4862-b91d-496665d15cce",
        requires_output_lock=0,
        execute="failedTransferCleanup",
        arguments='"fail" "%SIPUUID%" "%SIPDirectory%"',
    )
    TaskConfig.objects.create(
        id="6b2a7301-df99-4157-b09f-76e87e08f6d9",
        tasktype_id="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        tasktypepkreference="3362ef11-b4f1-4862-b91d-496665d15cce",
        description="Cleanup failed Transfer",
    )
    MicroServiceChainLink.objects.create(
        id="e780473a-0c10-431f-bab6-5d7238b2b70b",
        microservicegroup="Failed transfer",
        defaultexitmessage="Failed",
        currenttask_id="6b2a7301-df99-4157-b09f-76e87e08f6d9",
        defaultnextchainlink_id="377f8ebb-7989-4a68-9361-658079ff8138",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="f4abbac5-558b-4c2b-8f4f-cdf13cf57249",
        microservicechainlink_id="e780473a-0c10-431f-bab6-5d7238b2b70b",
        exitcode=0,
        nextmicroservicechainlink_id="377f8ebb-7989-4a68-9361-658079ff8138",
        exitmessage="Completed successfully",
    )
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="61c316a6-0a50-4f65-8767-1f44b1eeb6dd"
    ).update(nextmicroservicechainlink_id="e780473a-0c10-431f-bab6-5d7238b2b70b")

    # Add failedTransferCleanup script to rejected
    StandardTaskConfig.objects.create(
        id="72f11e68-7350-42a7-9bdc-60001d0505a2",
        requires_output_lock=0,
        execute="failedTransferCleanup",
        arguments='"reject" "%SIPUUID%" "%SIPDirectory%"',
    )
    TaskConfig.objects.create(
        id="1fea5138-981f-4fef-9d74-4d6328fb9248",
        tasktype_id="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        tasktypepkreference="72f11e68-7350-42a7-9bdc-60001d0505a2",
        description="Cleanup rejected transfer",
    )
    MicroServiceChainLink.objects.create(
        id="ae5cdd0d-2f81-4935-a380-d5c6f1337d93",
        microservicegroup="Reject transfer",
        defaultexitmessage="Failed",
        currenttask_id="1fea5138-981f-4fef-9d74-4d6328fb9248",
        defaultnextchainlink_id="333532b9-b7c2-4478-9415-28a3056d58df",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="e8b5ea83-a108-48b4-af8e-42fa6794b1de",
        microservicechainlink_id="ae5cdd0d-2f81-4935-a380-d5c6f1337d93",
        exitcode=0,
        nextmicroservicechainlink_id="333532b9-b7c2-4478-9415-28a3056d58df",
        exitmessage="Completed successfully",
    )
    MicroServiceChain.objects.filter(id="1b04ec43-055c-43b7-9543-bd03c6a778ba").update(
        startinglink_id="ae5cdd0d-2f81-4935-a380-d5c6f1337d93"
    )

    # Add parse external METS
    StandardTaskConfig.objects.create(
        id="d9708512-ac5f-4211-b07a-e5a41c6825b6",
        requires_output_lock=0,
        execute="parseExternalMETS",
        arguments='%SIPUUID% "%SIPDirectory%"',
    )
    TaskConfig.objects.create(
        id="9ecf18d4-652b-4bd2-a3f5-bfb5794299f8",
        tasktype_id="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        tasktypepkreference="d9708512-ac5f-4211-b07a-e5a41c6825b6",
        description="Parse external METS",
    )
    MicroServiceChainLink.objects.create(
        id="675acd22-828d-4949-adc7-1888240f5e3d",
        microservicegroup="Complete transfer",
        defaultexitmessage="Failed",
        currenttask_id="9ecf18d4-652b-4bd2-a3f5-bfb5794299f8",
        defaultnextchainlink_id="db99ab43-04d7-44ab-89ec-e09d7bbdc39d",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="575ab10a-560c-40ed-aa33-95a26ef52b65",
        microservicechainlink_id="675acd22-828d-4949-adc7-1888240f5e3d",
        exitcode=0,
        nextmicroservicechainlink_id="db99ab43-04d7-44ab-89ec-e09d7bbdc39d",
        exitmessage="Completed successfully",
    )
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc"
    ).update(nextmicroservicechainlink_id="675acd22-828d-4949-adc7-1888240f5e3d")
    MicroServiceChainLink.objects.filter(
        id="8ec0b0c1-79ad-4d22-abcd-8e95fcceabbc"
    ).update(defaultnextchainlink_id="675acd22-828d-4949-adc7-1888240f5e3d")
    TaskConfigUnitVariableLinkPull.objects.filter(
        id="49d853a9-646d-4e9f-b825-d1bcc3ba77f0"
    ).update(defaultmicroservicechainlink_id="675acd22-828d-4949-adc7-1888240f5e3d")


class Migration(migrations.Migration):

    dependencies = [("main", "0026_agent_m2m_event")]

    operations = [migrations.RunPython(data_migration)]
