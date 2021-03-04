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
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainChoice = apps.get_model("main", "MicroServiceChainChoice")

    # Set task types PKs
    get_user_choice_to_proceed_with = "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c"
    one_instance = "36b2e239-4a57-4aa5-8ebc-7a29139baca6"
    # Set chain PKs
    dip_store_chain_pk = "8d29eb3d-a8a8-4347-806e-3d8227ed44a1"
    dip_nop_chain_pk = "4500f34e-f004-4ccf-8720-5c38d0be2254"
    # Set link, task, etc. PKs
    dip_store_retrieve_locations_link_pk = "d026e5a4-96cf-4e4c-938d-a74b0d211da0"
    dip_store_retrieve_locations_task_pk = (
        "21292501-0c12-4376-8fb1-413286060dc2"  # Existing
    )

    dip_store_location_link_pk = "cd844b6e-ab3c-4bc6-b34f-7103f88715de"
    dip_store_location_task_pk = "55123c46-78c9-4b5d-ad92-2b1f3eb658af"

    dip_store_link_pk = "653b134f-4a37-4578-a286-7f2072e89f9e"
    dip_store_task_pk = "2dd14de8-62c7-49a5-bfa1-dd025e7a426b"
    dip_store_standard_task_pk = "1e4ccd56-a076-4aa2-9642-1ed8944b306a"

    dip_move_link_pk = "2e31580d-1678-474b-83e5-a53d97d150f6"
    dip_move_task_pk = "e485f0f4-7d44-45c6-a0d2-bba4b2abd0d0"

    dip_store_choice_link_pk = "5e58066d-e113-4383-b20b-f301ed4d751c"
    dip_store_choice_task_pk = "abf861ee-2125-4e7e-8d85-9e1dcd020b4b"

    email_fail_report_link_pk = "7d728c39-395f-4892-8193-92f086c0546f"

    nop_link_pk = "f8ee488b-5667-4417-ae15-bed9e42ee97d"
    nop_task_pk = "79ba8ce2-d01a-4723-83b7-5ac2b9ab2ae9"
    nop_standard_task_pk = "888281a1-9678-46ed-a1a0-be9f0c6d02b0"

    # Third link in chain to store DIP after upload: store DIP

    StandardTaskConfig.objects.create(
        id=dip_store_standard_task_pk,
        requires_output_lock=True,
        execute="storeAIP_v0.0",
        arguments='''"%DIPsStore%" "%watchDirectoryPath%uploadedDIPs/%SIPName%-%SIPUUID%" "%SIPUUID%" "%SIPName%" "DIP"''',
        lastmodified="2014-09-11 09:09:53",
    )
    TaskConfig.objects.create(
        id=dip_store_task_pk,
        tasktype_id=one_instance,
        tasktypepkreference=dip_store_standard_task_pk,
        description="Store DIP",
        lastmodified="2014-09-11 09:09:53",
    )
    MicroServiceChainLink.objects.create(
        id=dip_store_link_pk,
        currenttask_id=dip_store_task_pk,
        defaultnextchainlink_id=email_fail_report_link_pk,
        microservicegroup="Upload DIP",
        reloadfilelist=1,
        defaultexitmessage="Failed",
        lastmodified="2014-09-11 09:09:53",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="8d0f7de9-8efa-4574-868c-bc85ddeea1d9",
        microservicechainlink_id=dip_store_link_pk,
        exitcode=0,
        nextmicroservicechainlink_id=None,
        exitmessage="Completed successfully",
        lastmodified="2014-09-11 09:09:53",
    )

    # Second link in chain to store DIP after upload: ask for store DIP location
    MicroServiceChainLink.objects.create(
        id=dip_store_location_link_pk,
        currenttask_id=dip_store_location_task_pk,
        defaultnextchainlink_id=email_fail_report_link_pk,
        microservicegroup="Upload DIP",
        reloadfilelist=1,
        defaultexitmessage="Failed",
        lastmodified="2014-09-11 09:09:53",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="7d7455e7-ca01-4ff9-ab7e-f50ab70623f1",
        microservicechainlink_id=dip_store_location_link_pk,
        exitcode=0,
        nextmicroservicechainlink_id=dip_store_link_pk,
        exitmessage="Completed successfully",
        lastmodified="2014-09-11 09:09:53",
    )

    # First link in chain to store DIP after upload: retrieve storage locations
    MicroServiceChainLink.objects.create(
        id=dip_store_retrieve_locations_link_pk,
        currenttask_id=dip_store_retrieve_locations_task_pk,
        defaultnextchainlink_id=email_fail_report_link_pk,
        microservicegroup="Upload DIP",
        reloadfilelist=1,
        defaultexitmessage="Failed",
        lastmodified="2014-09-11 09:09:53",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="fc9b0f42-6893-4806-b575-ec954cd1c43d",
        microservicechainlink_id=dip_store_retrieve_locations_link_pk,
        exitcode=0,
        nextmicroservicechainlink_id=dip_store_location_link_pk,
        exitmessage="Completed successfully",
        lastmodified="2014-09-11 09:09:53",
    )

    # New chain to store DIP after upload
    MicroServiceChain.objects.create(
        id=dip_store_chain_pk,
        startinglink_id=dip_store_retrieve_locations_link_pk,
        description="Store DIP",
        lastmodified="2014-09-11 09:09:53",
    )

    # Link in chain for confirming post-upload completion without storage
    StandardTaskConfig.objects.create(
        id=nop_standard_task_pk,
        requires_output_lock=False,
        execute="echo_v0.0",
        arguments='"Completed."',
        lastmodified="2012-10-01 17:25:01",
    )
    TaskConfig.objects.create(
        id=nop_task_pk,
        tasktype_id=one_instance,
        tasktypepkreference=nop_standard_task_pk,
        description="Completed",
        lastmodified="2012-10-01 17:25:11",
    )
    MicroServiceChainLink.objects.create(
        id=nop_link_pk,
        currenttask_id=nop_task_pk,
        microservicegroup="Upload DIP",
        reloadfilelist=1,
        defaultexitmessage="Failed",
        lastmodified="2012-10-01 17:25:06",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="fc8b0f42-6893-4806-b575-ec954cd1c43d",
        microservicechainlink_id=nop_link_pk,
        exitcode=0,
        nextmicroservicechainlink_id=None,
        exitmessage="Completed successfully",
        lastmodified="2014-09-11 09:09:53",
    )

    # New chain for confirming post-upload completion without storage
    MicroServiceChain.objects.create(
        id=dip_nop_chain_pk,
        startinglink_id=nop_link_pk,
        description="Do not store",
        lastmodified="2014-09-11 09:09:53",
    )

    # Second link in store DIP choice chain: choose whether to store DIP
    TaskConfig.objects.create(
        id=dip_store_choice_task_pk,
        tasktype_id=get_user_choice_to_proceed_with,
        description="Store DIP?",
        lastmodified="2012-10-01 17:25:11",
    )
    MicroServiceChainLink.objects.create(
        id=dip_store_choice_link_pk,
        currenttask_id=dip_store_choice_task_pk,
        microservicegroup="Upload DIP",
        reloadfilelist=1,
        defaultexitmessage="Failed",
        lastmodified="2012-10-01 17:25:06",
    )
    MicroServiceChainChoice.objects.create(
        id="6ffac4ac-7b5c-4ebb-880c-ecc7588c0b51",
        choiceavailableatlink_id=dip_store_choice_link_pk,
        chainavailable_id=dip_store_chain_pk,
        lastmodified="2014-09-11 09:09:53",
    )
    MicroServiceChainChoice.objects.create(
        id="6ffac4ac-7b5c-4ebb-880c-ecc7588c0b50",
        choiceavailableatlink_id=dip_store_choice_link_pk,
        chainavailable_id=dip_nop_chain_pk,
        lastmodified="2014-09-11 09:09:53",
    )

    # First link in store DIP choice chain: copy to uploadedDIPs
    MicroServiceChainLink.objects.create(
        id=dip_move_link_pk,
        currenttask_id=dip_move_task_pk,
        microservicegroup="Upload DIP",
        reloadfilelist=1,
        defaultexitmessage="Failed",
        lastmodified="2012-10-01 17:25:06",
    )
    MicroServiceChainLinkExitCode.objects.create(
        id="c4bd05e3-d7b9-4c67-a153-40b760e30eb7",
        microservicechainlink_id=dip_move_link_pk,
        exitcode=0,
        nextmicroservicechainlink_id=dip_store_choice_link_pk,
        exitmessage="Completed successfully",
        lastmodified="2012-10-01 17:25:07",
    )

    # New chain for choice as to whether to store DIP after upload
    MicroServiceChain.objects.create(
        id="d456dfde-1cdb-4178-babc-1a4537fe1b87",
        startinglink_id=dip_move_link_pk,
        description="Store DIP",
        lastmodified="2014-09-11 09:09:53",
    )

    # Update upload links to direct to new chain
    upload_atom_tail = "651236d2-d77f-4ca7-bfe9-6332e96608ff"
    upload_cdm_tail = "f12ece2c-fb7e-44de-ba87-7e3c5b6feb74"
    upload_atk_tail = "bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1"
    upload_as_tail = "ff89a530-0540-4625-8884-5a2198dea05a"
    store_start_link_pk = dip_move_link_pk

    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink_id__in=(
            upload_atom_tail,
            upload_cdm_tail,
            upload_atk_tail,
            upload_as_tail,
        )
    ).update(nextmicroservicechainlink_id=store_start_link_pk)
    MicroServiceChainLink.objects.filter(
        id__in=(upload_atom_tail, upload_cdm_tail, upload_atk_tail, upload_as_tail)
    ).update(defaultnextchainlink_id=store_start_link_pk)


class Migration(migrations.Migration):

    dependencies = [("main", "0009_matching_gui")]

    operations = [migrations.RunPython(data_migration)]
