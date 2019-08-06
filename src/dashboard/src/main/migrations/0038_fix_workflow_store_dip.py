# -*- coding: utf-8 -*-
"""Migration to change workflow related to DIP upload and storage."""
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    """This migration modifies the workflow related to uploading and storing
    of DIPs. The end result is the sub-workflow schematized below:

                                    Upload DIP?
                                       /  \
                                     Yes   No
                                    /      |
                              Atom, etc.   |
                                 /         |
                            move to        |
                            uploadedDIPs/  |
                                         \ |
                                      Store DIP?
                                         /  \
                                       Yes   No
                                       |     |
                               Store on SS   If uploaded, do nothing
                                             If NOT uploaded, move to rejected

    The workflow above is better for the following reaons:

    1. There is only one "Store DIP Location" choice, so it can more easily
       be made a preconfigured choice within the current system
    2. It is more clear that when a DIP is neither uploaded nor stored, it is
       rejected.

    Steps:

    1. Remove "Reject DIP" from options at "Upload DIP" decision point.

    2. Rename the "Store DIP" chain's description to "Do Not Upload DIP" and
       set its starting link to the "Store DIP?" question.

    3. Remove the unused links and their dependencies:

       - "Retrieve DIP Storage Locations" (ed5d8475-3793-4fb0-a8df-94bd79b26a4c)
       - "Store DIP location" (b7a83da6-ed5a-47f7-a643-1e9f9f46e364)
       - "Store DIP" (e85a01f1-4061-4049-8922-5694b25c23a2)
       - "Move to the uploadedDIPs directory"
         (e3efab02-1860-42dd-a46c-25601251b930)

    4. Change "Completed" link to "Handle unstored DIP". This is handled by a
       new client script that moves the DIP to the rejected/ directory iff it
       has NOT been uploaded.

    5. Change "move" to "copy" in "move to uploadedDIPS dectory" so that the
       SIP is still where MCPServer expects it to be and preconfigured choices
       can work for Store DIP and Store DIP locations.
    """
    ###########################################################################
    # Model Classes
    ###########################################################################

    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainChoice = apps.get_model("main", "MicroServiceChainChoice")
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    TaskConfig = apps.get_model("main", "TaskConfig")

    ###########################################################################
    # Useful Model Instances
    ###########################################################################

    # The "Reject DIP" chain/link will be destroyed.
    reject_dip_chain_choice_uuid = "39bcba03-d251-4974-8a7b-45b2444e19a8"
    reject_dip_link_uuid = "f2a1faaf-7322-4d9c-aff9-f809e7a6a6a2"
    reject_dip_chain_uuid = "eea54915-2a85-49b7-a370-b1a250dd29ce"
    reject_dip_tc_uuid = "ea331cfb-d4f2-40c0-98b5-34d21ee6ad3e"
    reject_dip_stc_uuid = "4f7e2ed6-44b9-49a7-a1b7-bbfe58eadea8"

    # "Store DIP" chain: its description will be changed to "Do Not Upload DIP"
    # and its starting link will be the "Store DIP?" decision point.
    store_dip_quest_link_uuid = "5e58066d-e113-4383-b20b-f301ed4d751c"

    # Links to prune (destroy)
    dstry_retrieve_locat_link_uuid = "ed5d8475-3793-4fb0-a8df-94bd79b26a4c"
    dstry_store_dip_locat_link_uuid = "b7a83da6-ed5a-47f7-a643-1e9f9f46e364"
    dstry_store_dip_link_uuid = "e85a01f1-4061-4049-8922-5694b25c23a2"
    dstry_move_uploaded_link_uuid = "e3efab02-1860-42dd-a46c-25601251b930"

    # "Completed" link becomes "Handle unstored DIP" and its STC references a
    # new execute (and arguments), which is a new client script that moves the
    # DIP to the rejected/ directory iff it has NOT been uploaded.
    completed_link_uuid = "f8ee488b-5667-4417-ae15-bed9e42ee97d"
    completed_stc_uuid = "888281a1-9678-46ed-a1a0-be9f0c6d02b0"

    upload_dip_choice_link_uuid = "92879a29-45bf-4f0b-ac43-e64474f0f2f9"

    ###########################################################################
    # 1. Remove "Reject DIP" from options at "Upload DIP" decision point:
    ###########################################################################

    # Destroy the "Reject DIP" chain and link and attendant models.
    # Deleting just the task config models is sufficient to delete the relevant
    # MS chain, choice and link models because of Django's default cascading
    # delete behaviour for foreign keys.
    # See https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.CASCADE
    StandardTaskConfig.objects.get(id=reject_dip_stc_uuid).delete()
    TaskConfig.objects.get(id=reject_dip_tc_uuid).delete()
    try:
        MicroServiceChainChoice.objects.get(id=reject_dip_chain_choice_uuid).delete()
    except MicroServiceChainChoice.DoesNotExist:
        print("Chain choice {} does not exist".format(reject_dip_chain_choice_uuid))
    try:
        MicroServiceChainLink.objects.get(id=reject_dip_link_uuid).delete()
    except MicroServiceChainLink.DoesNotExist:
        print("Chain link {} does not exist".format(reject_dip_link_uuid))
    try:
        MicroServiceChain.objects.get(id=reject_dip_chain_uuid).delete()
    except MicroServiceChain.DoesNotExist:
        print("Chain {} does not exist".format(reject_dip_chain_uuid))

    ###########################################################################
    # 2. Modifications to the "Store DIP" chain
    ###########################################################################

    new_store_dip_chain_id = "6eb8ebe7-fab3-4e4c-b9d7-14de17625baa"
    MicroServiceChain.objects.create(
        id=new_store_dip_chain_id,
        startinglink_id=store_dip_quest_link_uuid,
        description="Do not upload DIP",
    )

    MicroServiceChainChoice.objects.create(
        id="6513c071-9b99-4e7c-b0c7-8792ff9cb273",
        choiceavailableatlink_id=upload_dip_choice_link_uuid,
        chainavailable_id=new_store_dip_chain_id,
    )

    ###########################################################################
    # 3. Remove the unused links and their dependencies
    ###########################################################################

    MicroServiceChainLink.objects.get(id=dstry_retrieve_locat_link_uuid).delete()
    MicroServiceChainLink.objects.get(id=dstry_store_dip_locat_link_uuid).delete()
    MicroServiceChainLink.objects.get(id=dstry_store_dip_link_uuid).delete()
    MicroServiceChainLink.objects.get(id=dstry_move_uploaded_link_uuid).delete()

    ###########################################################################
    # 4. Change "Completed" link to "Handle unstored DIP"
    ###########################################################################

    completed_link = MicroServiceChainLink.objects.get(id=completed_link_uuid)
    completed_tc = completed_link.currenttask
    completed_tc.description = "Handle unstored DIP"
    completed_tc.save()
    completed_stc = StandardTaskConfig.objects.get(id=completed_stc_uuid)
    completed_stc.arguments = (
        '"%SIPDirectory%" '
        '"%rejectedDirectory%" '
        '"%watchDirectoryPath%uploadedDIPs/"'
    )
    completed_stc.execute = "handleUnstoredDIP_v0.0"
    completed_stc.save()

    ###########################################################################
    # 5. Change "move" to "copy" in "move to uploadedDIPS dectory"
    ###########################################################################

    # By using copy_v0.0, the MCPServer will know where to look for the
    # processing config XML file, viz. in the uploadDIP/ directory.
    # UPDATE StandardTasksConfigs SET execute = 'copy_v0.0', arguments = '"%SIPDirectory%" "%watchDirectoryPath%uploadedDIPs/." -R' WHERE pk = '302be9f9-af3f-45da-9305-02706d81b742';
    move_uploaded_dips_stc_uuid = "302be9f9-af3f-45da-9305-02706d81b742"
    StandardTaskConfig.objects.filter(id=move_uploaded_dips_stc_uuid).update(
        execute="copy_v0.0",
        arguments='"%SIPDirectory%" ' '"%watchDirectoryPath%uploadedDIPs/." ' "-R",
    )


class Migration(migrations.Migration):

    dependencies = [("main", "0037_mediaconch_policy_checks")]

    operations = [migrations.RunPython(data_migration)]
