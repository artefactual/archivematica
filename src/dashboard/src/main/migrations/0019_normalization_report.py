# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    TaskConfig = apps.get_model("main", "TaskConfig")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")

    one_instance_task_type = "36b2e239-4a57-4aa5-8ebc-7a29139baca6"
    move_to_approve_normalization_mscl = "c2e6600d-cd26-42ed-bed5-95d41c06e37b"

    normalization_report_stc = "59531c29-59d3-468d-897c-9800c4525f81"
    normalization_report_tc = "17aa7180-ded8-45c7-96d0-5ecebfd1a5cf"
    normalization_report_mscl = "3a70bc05-fa82-4067-a069-a56b6006be0a"

    # Introduce new normalization report microservice
    StandardTaskConfig.objects.create(
        id=normalization_report_stc,
        requires_output_lock=False,
        execute="normalizeReport_v0.0",
        arguments='''--uuid "%SIPUUID%"''',
    )
    TaskConfig.objects.create(
        id=normalization_report_tc,
        tasktype_id=one_instance_task_type,
        tasktypepkreference=normalization_report_stc,
        description="Normalization report",
    )
    MicroServiceChainLink.objects.create(
        id=normalization_report_mscl,
        currenttask_id=normalization_report_tc,
        defaultnextchainlink_id=move_to_approve_normalization_mscl,
        microservicegroup="Normalize",
        defaultexitmessage="Failed",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="cbf1b16e-5260-4548-ba80-eeeaf5e54cc2",
        microservicechainlink_id=normalization_report_mscl,
        exitcode=0,
        nextmicroservicechainlink_id=move_to_approve_normalization_mscl,
        exitmessage="Completed successfully",
    )

    # Introduce between "Remove files without linking information" and "Move to approve normalization"
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="dba3028d-2029-4a87-9992-f6335d890528"
    ).update(nextmicroservicechainlink_id=normalization_report_mscl)


class Migration(migrations.Migration):

    dependencies = [("main", "0018_archivesspace_sip_arrange")]

    operations = [migrations.RunPython(data_migration)]
