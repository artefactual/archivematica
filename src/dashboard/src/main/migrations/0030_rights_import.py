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

    one_instance_task_type = "36b2e239-4a57-4aa5-8ebc-7a29139baca6"
    characterize_and_extract_md_mscl = "303a65f6-a16f-4a06-807b-cb3425a30201"
    fail_mscl = "61c316a6-0a50-4f65-8767-1f44b1eeb6dd"

    rights_import_stc = "82579891-1cb7-486e-a0a6-b4cdf99c282f"
    rights_import_tc = "637cc23a-c5f5-4df5-a352-5d47014be63b"
    rights_import_mscl = "1a136608-ae7b-42b4-bf2f-de0e514cfd47"

    # Introduce new rights import microservice
    StandardTaskConfig.objects.create(
        id=rights_import_stc,
        requires_output_lock=False,
        execute="rightsFromCSV_v0.0",
        arguments="""%SIPUUID%'' ''%SIPDirectory%metadata/rights.csv""",
    )
    TaskConfig.objects.create(
        id=rights_import_tc,
        tasktype_id=one_instance_task_type,
        tasktypepkreference=rights_import_stc,
        description="Load rights",
    )
    MicroServiceChainLink.objects.create(
        id=rights_import_mscl,
        currenttask_id=rights_import_tc,
        defaultnextchainlink_id=fail_mscl,
        microservicegroup="Characterize and extract metadata",
        defaultexitmessage="Failed",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="2817a47f-02f3-4b8a-9536-f1eebbcdb8c0",
        microservicechainlink_id=rights_import_mscl,
        exitcode=0,
        nextmicroservicechainlink_id=characterize_and_extract_md_mscl,
        exitmessage="Completed successfully",
    )

    # Introduce between "Add processed structMap to METS.xml document" and "Characterize and extract"
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id="307edcde-ad10-401c-92c4-652917c993ed"
    ).update(nextmicroservicechainlink_id=rights_import_mscl)


class Migration(migrations.Migration):

    dependencies = [("main", "0029_backlog_removal_event")]

    operations = [migrations.RunPython(data_migration)]
