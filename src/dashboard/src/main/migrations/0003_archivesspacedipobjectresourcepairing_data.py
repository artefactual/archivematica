# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    # The new chain - begins with selecting config, then calls upload script.
    # The magic that pops open a new window happens in the dashboard UI, and isn't handled here.
    archivesspace_upload_chain = "3572f844-5e69-4000-a24b-4e32d3487f82"
    archivesspace_select_config_tc = "5ded9d05-dd24-484a-a8b2-73ec5d35aa63"
    archivesspace_select_config_mscl = "a0db8294-f02a-4f49-a557-b1310a715ffc"

    # Add the new DIP upload script
    archivesspace_upload_stc = "10a0f352-aeb7-4c13-8e9e-e81bda9bca29"
    archivesspace_upload_tc = "71eaef05-264d-453e-b8c4-7b7e2c7ac889"
    archivesspace_upload_mscl = "ff89a530-0540-4625-8884-5a2198dea05a"

    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfig = apps.get_model("main", "TaskConfig")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainChoice = apps.get_model("main", "MicroServiceChainChoice")
    MicroServiceChoiceReplacementDic = apps.get_model(
        "main", "MicroServiceChoiceReplacementDic"
    )

    StandardTaskConfig.objects.create(
        id=archivesspace_upload_stc,
        execute="upload-archivesspace_v0.0",
        arguments='''--host "%host%" --port "%port%" --user "%user%" --passwd "%passwd%" --dip_location "%SIPDirectory%" --dip_name "%SIPName%" --dip_uuid "%SIPUUID%" --restrictions "%restrictions%" --object_type "%object_type%" --xlink_actuate "%xlink_actuate%" --xlink_show "%xlink_show%" --use_statement "%use_statement%" --uri_prefix "%uri_prefix%" --access_conditions "%access_conditions%" --use_conditions "%use_conditions%"''',
    )
    TaskConfig.objects.create(
        id=archivesspace_upload_tc,
        tasktype_id="36b2e239-4a57-4aa5-8ebc-7a29139baca6",
        tasktypepkreference=archivesspace_upload_stc,
        description="Upload to ArchivesSpace",
    )
    MicroServiceChainLink.objects.create(
        id=archivesspace_upload_mscl,
        currenttask_id=archivesspace_upload_tc,
        defaultnextchainlink_id="e3efab02-1860-42dd-a46c-25601251b930",
        microservicegroup="Upload DIP",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="aa18a6d3-5d08-4827-99e7-b52abddcb812",
        microservicechainlink_id=archivesspace_upload_mscl,
        exitcode=0,
        nextmicroservicechainlink_id=None,
    )

    # MSCL for "choose config"
    # Empty string for taskTypePKReference is intentional; this is consistent with ArchivistsToolkit.
    TaskConfig.objects.create(
        id=archivesspace_select_config_tc,
        tasktype_id="9c84b047-9a6d-463f-9836-eafa49743b84",
        tasktypepkreference="",
        description="Choose Config for ArchivesSpace DIP Upload",
    )
    MicroServiceChainLink.objects.create(
        id=archivesspace_select_config_mscl,
        currenttask_id=archivesspace_select_config_tc,
        defaultnextchainlink_id=archivesspace_upload_mscl,
        microservicegroup="Upload DIP",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="1f53c86a-0afc-4eda-861d-c1501cb40e04",
        microservicechainlink_id=archivesspace_select_config_mscl,
        exitcode=0,
        nextmicroservicechainlink_id=archivesspace_upload_mscl,
    )

    # Create a new chain, beginning with "choose config", then insert a choice in the "Upload DIP?" choice
    MicroServiceChain.objects.create(
        id=archivesspace_upload_chain,
        startinglink_id=archivesspace_select_config_mscl,
        description="Upload DIP to ArchivesSpace",
    )
    MicroServiceChainChoice.objects.create(
        id="96fecb69-c020-4b54-abfb-2b157afe5cdb",
        choiceavailableatlink_id="92879a29-45bf-4f0b-ac43-e64474f0f2f9",
        chainavailable_id=archivesspace_upload_chain,
    )

    # Insert a dummy ReplacementDict for ArchivesSpace, which will be replaced the first time the user saves anything in the settings
    MicroServiceChoiceReplacementDic.objects.create(
        id="f8749dd2-0923-4b57-a074-45cd92ace56f",
        choiceavailableatlink_id=archivesspace_select_config_mscl,
        description="ArchivesSpace Config",
        replacementdic="""ArchivesSpace Config', '{"%port%": "8089", "%object_type%": "", "%host%": "localhost", "%xlink_show%": "new", "%use_statement%": "Image-Service", "%uri_prefix%": "http://www.example.com/", "%xlink_actuate%": "onRequest", "%access_conditions%": "", "%use_conditions%": "", "%restrictions%": "premis", "%passwd%": "admin", "%user%": "admin"}""",
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0003_archivesspacedipobjectresourcepairing")]

    operations = [migrations.RunPython(data_migration)]
