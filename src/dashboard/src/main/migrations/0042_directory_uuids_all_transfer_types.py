# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """Creates "Assign UUIDs to Directories" micro-service chain links for the
    remaining four transfer types. The migration at 0040_directory_model
    incorrectly only created the relevant links for Standard transfer types.
    This adds the relevant links at appropriate points in the workflow for
    Bag, DSpace, maildir, and TRIM transfers.

    It is crucial that the UUID assigning links occur after any restructuring
    and after the processing MCP XML config is placed into the transfer. If
    either of these conditions does not hold, then incorrect directory paths
    could be given UUIDs or processing configurations for directory UUID
    assignation could fail.

    In short, this results in the following general configuration in 4 distinct
    locations in the workflow.

    1. previous chain link
    2. "Assign UUIDs to directories?" chain link
    3. "Assign UUIDs to directories" chain link
    4. next chain link
    """

    TaskConfig = apps.get_model("main", "TaskConfig")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    MicroServiceChoiceReplacementDic = apps.get_model(
        "main", "MicroServiceChoiceReplacementDic"
    )

    # TaskConfig that performs "Assign UUIDs to directories"
    dir_uuid_task_cfg_uuid = "388a277b-2463-4d11-b203-fc5b80a08f69"
    dir_uuid_task_cfg = TaskConfig.objects.get(id=dir_uuid_task_cfg_uuid)

    # TaskConfig that asks "Assign UUIDs to directories?"
    dir_uuid_choice_task_cfg_uuid = "f0c4abd3-1947-4d11-b78b-a55078460100"
    dir_uuid_choice_task_cfg = TaskConfig.objects.get(id=dir_uuid_choice_task_cfg_uuid)

    # We iterate through each of these four transfer types and create the new
    # links before ``next_chain_link_uuid`` and after
    # ``previous_chain_link_uuid``. All other UUIDs in this dict are newly
    # minted here.
    transfer_types = {
        "bag": {
            "next_chain_link_uuid": "3409b898-e532-49d3-98ff-a2a1f9d988fa",
            "previous_chain_link_uuid": "46e19522-9a71-48f1-9ccd-09cabfba3f38",
            "dir_uuid_chain_link_uuid": "5415c813-3637-49ab-afec-9b435c2e4d2c",
            "dir_uuid_choice_chain_link_uuid": "8882bad4-561c-4126-89c9-f7f0c083d5d7",
            "no_choice": "0053c670-3e61-4a3e-a188-3a2dd1eda426",
            "yes_choice": "7e4cf404-e62d-4dc2-8d81-6141e390f66f",
            "exit_code_0_to_uuids_dirs": "6eadb699-4505-40f2-aff4-00d020bbf532",
            "exit_code_0_to_uuids_objs": "57026d55-186e-4601-9a30-91270d4f1c94",
        },
        "trim": {
            "next_chain_link_uuid": "3409b898-e532-49d3-98ff-a2a1f9d988fa",
            "previous_chain_link_uuid": "e399bd60-202d-42df-9760-bd14497b5034",
            "dir_uuid_chain_link_uuid": "f954326a-250b-4666-b2f2-1e54d36958a1",
            "dir_uuid_choice_chain_link_uuid": "e10a31c3-56df-4986-af7e-2794ddfe8686",
            "no_choice": "8e93e523-86bb-47e1-a03a-4b33e13f8c5e",
            "yes_choice": "2732a043-b197-4cbc-81ab-4e2bee9b74d3",
            "exit_code_0_to_uuids_dirs": "25fc25a4-c7b2-4904-8e0d-68087690adc4",
            "exit_code_0_to_uuids_objs": "7213fd30-d19b-4382-8395-7178f993473f",
        },
        "dspace": {
            "next_chain_link_uuid": "52269473-5325-4a11-b38a-c4aafcbd8f54",
            "previous_chain_link_uuid": "209400c1-5619-4acc-b091-b9d9c8fbb1c0",
            "dir_uuid_chain_link_uuid": "b08ad32b-f94f-4c2a-9fb0-9ef9328718dd",
            "dir_uuid_choice_chain_link_uuid": "d6f6f5db-4cc2-4652-9283-9ec6a6d181e5",
            "no_choice": "6dfbeff8-c6b1-435b-833a-ed764229d413",
            "yes_choice": "aa793efa-1b62-498c-8f92-cab187a99a2a",
            "exit_code_0_to_uuids_dirs": "b24a85a8-6180-444c-a3cb-6033b9974858",
            "exit_code_0_to_uuids_objs": "6167489b-a218-42be-9faa-cd120a742073",
        },
        "maildir": {
            "next_chain_link_uuid": "66c9c178-2224-41c6-9c0b-dcb60ff57b1a",
            "previous_chain_link_uuid": "f8319d49-f1e3-45dd-a404-66165c59dec7",
            "dir_uuid_chain_link_uuid": "960f6db0-5b41-417c-bedc-a0eb75a82227",
            "dir_uuid_choice_chain_link_uuid": "1563f22f-f5f7-4dfe-a926-6ab50d408832",
            "no_choice": "dc0ee6b6-ed5f-42a3-bc8f-c9c7ead03ed1",
            "yes_choice": "efd98ddb-80a6-4206-80bf-81bf00f84416",
            "exit_code_0_to_uuids_dirs": "35f02064-dfa3-45fb-a845-422e4ead4479",
            "exit_code_0_to_uuids_objs": "c8dc3982-2759-498e-8a06-2ff9f0ec3388",
        },
    }

    for meta in transfer_types.values():

        next_chain_link = MicroServiceChainLink.objects.get(
            id=meta["next_chain_link_uuid"]
        )

        previous_chain_link = MicroServiceChainLink.objects.get(
            id=meta["previous_chain_link_uuid"]
        )

        dir_uuid_chain_link = MicroServiceChainLink.objects.create(
            id=meta["dir_uuid_chain_link_uuid"],
            microservicegroup=previous_chain_link.microservicegroup,
            defaultexitmessage="Failed",
            currenttask=dir_uuid_task_cfg,
            replaces_id=None,
            defaultnextchainlink=next_chain_link,
        )

        dir_uuid_choice_chain_link = MicroServiceChainLink.objects.create(
            id=meta["dir_uuid_choice_chain_link_uuid"],
            microservicegroup=previous_chain_link.microservicegroup,
            defaultexitmessage="Failed",
            currenttask=dir_uuid_choice_task_cfg,
            replaces_id=None,
            defaultnextchainlink=dir_uuid_chain_link,
        )

        MicroServiceChoiceReplacementDic.objects.create(
            id=meta["no_choice"],
            description="No",
            replacementdic='{"%AssignUUIDsToDirectories%": "False"}',
            choiceavailableatlink=dir_uuid_choice_chain_link,
            replaces_id=None,
        )

        MicroServiceChoiceReplacementDic.objects.create(
            id=meta["yes_choice"],
            description="Yes",
            replacementdic='{"%AssignUUIDsToDirectories%": "True"}',
            choiceavailableatlink=dir_uuid_choice_chain_link,
            replaces_id=None,
        )

        MicroServiceChainLinkExitCode.objects.create(
            id=meta["exit_code_0_to_uuids_objs"],
            microservicechainlink=dir_uuid_chain_link,
            exitcode=0,
            exitmessage=2,
            nextmicroservicechainlink=next_chain_link,
        )

        MicroServiceChainLinkExitCode.objects.create(
            id=meta["exit_code_0_to_uuids_dirs"],
            microservicechainlink=dir_uuid_choice_chain_link,
            exitcode=0,
            exitmessage=2,
            nextmicroservicechainlink=dir_uuid_chain_link,
        )

        MicroServiceChainLinkExitCode.objects.filter(
            microservicechainlink=previous_chain_link
        ).update(nextmicroservicechainlink=dir_uuid_choice_chain_link)
        previous_chain_link.defaultnextchainlink = dir_uuid_choice_chain_link


class Migration(migrations.Migration):

    dependencies = [("main", "0041_bind_pids")]

    operations = [migrations.RunPython(data_migration)]
