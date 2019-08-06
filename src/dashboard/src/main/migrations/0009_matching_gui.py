# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfig = apps.get_model("main", "TaskConfig")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )

    StandardTaskConfig.objects.create(
        pk="cbe200ab-a634-4902-a0e6-8ed1858538d4",
        requires_output_lock=False,
        execute="dipGenerationHelper",
        arguments='--sipUUID "%SIPUUID%" --sipPath "%SIPDirectory%"',
    )
    TaskConfig.objects.create(
        pk="5e0ac12e-6ce7-4d11-bd75-e14167210df4",
        tasktype_id="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        tasktypepkreference="cbe200ab-a634-4902-a0e6-8ed1858538d4",
        description="Pre-processing for DIP generation",
    )
    MicroServiceChainLink.objects.create(
        pk="5749c11f-ed08-4965-8d8e-1473b1016073",
        microservicegroup="Prepare DIP",
        defaultexitmessage="Failed",
        currenttask_id="5e0ac12e-6ce7-4d11-bd75-e14167210df4",
        defaultnextchainlink_id="7d728c39-395f-4892-8193-92f086c0546f",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="4447a11c-5c3b-4092-91fa-de613317cc82",
        microservicechainlink_id="5749c11f-ed08-4965-8d8e-1473b1016073",
        exitcode=0,
        nextmicroservicechainlink_id="61a8de9c-7b25-4f0f-b218-ad4dde261eed",
        exitmessage="Completed successfully",
    )
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="6ee25a55-7c08-4c9a-a114-c200a37146c4"
    ).update(nextmicroservicechainlink_id="5749c11f-ed08-4965-8d8e-1473b1016073")


class Migration(migrations.Migration):

    dependencies = [("main", "0008_fpcommandoutput")]

    operations = [migrations.RunPython(data_migration)]
