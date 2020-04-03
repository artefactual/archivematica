# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations, models
import main.models


def data_migration(apps, schema_editor):
    """Creates the ``Directory`` model, primarily so that directories can be
    assigned UUIDs and can be documented in the METS.

    This migration modifies the workflow so that there are two new
    micro-services, i.e., chain links, one which asks the user whether to
    assign UUIDs to directories and the another which actually does it.

    Creation steps:

    1. Create new Micro-service chain link "Assign UUIDs to directories"
    2. Create new Micro-service *choice* chain link "Assign UUIDs to
       directories?"

    Positioning steps:

    1. Position "Assign UUIDs to directories" after "Assign UUIDs to
       directories?" and before "Assign file UUIDs to objects".
    1. Position "Assign UUIDs to directories?" after "Set file permissions".

    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    TaskType = apps.get_model("main", "TaskType")
    TaskConfig = apps.get_model("main", "TaskConfig")
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    MicroServiceChoiceReplacementDic = apps.get_model(
        "main", "MicroServiceChoiceReplacementDic"
    )
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")

    ###########################################################################
    # Useful Model Instances
    ###########################################################################

    # This is the "get replacement dic from user choice" TaskType.
    repl_dic_usr_choice_task_type = TaskType.objects.get(
        description="get replacement dic from user choice"
    )

    # This is the TaskType that handles client scripts that treat an entire
    # directory (i.e., Transfer) in one go.
    entire_directory_task_type = TaskType.objects.get(description="one instance")

    # We need to position the two "Assign UUIDs to directories" chain links so
    # that:
    # - "Assign file UUIDs and checksums: Set file permissions" comes before, and
    # - "Assign file UUIDs and checksums: Assign file UUIDs to objects" comes after

    # Chain Link after is "Assign file UUIDs and checksums: Assign file UUIDs to
    # objects". Its UUID is dc144ff4-ad74-4a6e-ac15-b0beedcaf662.
    # Note that there is no obvious (to me) way to query this object because there
    # are 3 that match the following query, i.e., this one, as well as one each for
    # DSpace and Maildir transfer types (i.e., chains)::
    #
    #     MicroServiceChainLink.objects.filter(
    #         currenttask__description='Assign file UUIDs to objects',
    #         microservicegroup='Assign file UUIDs and checksums'
    #     )
    assign_uuids_objects_chain_link_uuid = "dc144ff4-ad74-4a6e-ac15-b0beedcaf662"
    assign_uuids_objects_chain_link = MicroServiceChainLink.objects.get(
        id=assign_uuids_objects_chain_link_uuid
    )

    # Chain Link before is "Include default Transfer processingMCP.xml: Include
    # default Transfer processingMCP.xml".
    # Its UUID is 0c96c798-9ace-4c05-b3cf-243cdad796b7.
    assign_uuids_file_perm_chain_link_uuid = "0c96c798-9ace-4c05-b3cf-243cdad796b7"
    assign_uuids_file_perm_chain_link = MicroServiceChainLink.objects.get(
        id=assign_uuids_file_perm_chain_link_uuid
    )

    ###########################################################################
    # New Chain Link: "Assign UUIDs to directories"
    ###########################################################################

    # StandardTaskConfig that performs "Assign UUIDs to directories"
    dir_uuid_stc_uuid = "91096265-d582-46be-b606-4769fc27c7a7"
    StandardTaskConfig.objects.create(
        id=dir_uuid_stc_uuid,
        execute="assignUUIDsToDirectories_v0.0",
        arguments=(
            '"%SIPDirectory%" "%SIPUUID%" --include-dirs'
            ' "%AssignUUIDsToDirectories%"'
        ),
    )

    # TaskConfig that performs "Assign UUIDs to directories"
    dir_uuid_task_cfg_uuid = "388a277b-2463-4d11-b203-fc5b80a08f69"
    dir_uuid_task_cfg = TaskConfig.objects.create(
        id=dir_uuid_task_cfg_uuid,
        tasktype=entire_directory_task_type,
        description="Assign UUIDs to directories",
        tasktypepkreference=dir_uuid_stc_uuid,
        replaces_id=None,
    )

    # MSChainLink that performs "Assign UUIDs to directories"
    dir_uuid_chain_link_uuid = "6441980c-b64b-447e-abc7-9351a2547f6a"
    dir_uuid_chain_link = MicroServiceChainLink.objects.create(
        id=dir_uuid_chain_link_uuid,
        microservicegroup="Assign file UUIDs and checksums",
        defaultexitmessage="Failed",
        currenttask=dir_uuid_task_cfg,
        replaces_id=None,
        # Comes before existing "Assign file UUIDs to objects" chain link.
        defaultnextchainlink=assign_uuids_objects_chain_link,
    )

    ###########################################################################
    # New Choice Chain Link: "Assign UUIDs to directories?"
    ###########################################################################

    # TaskConfig that asks "Assign UUIDs to directories?"
    dir_uuid_choice_task_cfg_uuid = "f0c4abd3-1947-4d11-b78b-a55078460100"
    dir_uuid_choice_task_cfg = TaskConfig.objects.create(
        id=dir_uuid_choice_task_cfg_uuid,
        tasktype=repl_dic_usr_choice_task_type,
        description="Assign UUIDs to directories?",
        tasktypepkreference=None,
        replaces_id=None,
    )

    # MSChainLink that asks "Assign UUIDs to directories?"
    dir_uuid_choice_chain_link_uuid = "bd899573-694e-4d33-8c9b-df0af802437d"
    dir_uuid_choice_chain_link = MicroServiceChainLink.objects.create(
        id=dir_uuid_choice_chain_link_uuid,
        microservicegroup="Assign file UUIDs and checksums",
        defaultexitmessage="Failed",
        currenttask=dir_uuid_choice_task_cfg,
        replaces_id=None,
        # Comes before chain link created above
        defaultnextchainlink=dir_uuid_chain_link,
    )

    # Create the "No" choice, i.e., "No, do not assign UUIDs to directories".
    MicroServiceChoiceReplacementDic.objects.create(
        id="891f60d0-1ba8-48d3-b39e-dd0934635d29",
        description="No",
        replacementdic='{"%AssignUUIDsToDirectories%": "False"}',
        choiceavailableatlink=dir_uuid_choice_chain_link,
        replaces_id=None,
    )

    # Create the "Yes" choice, i.e., "Yes, do assign UUIDs to directories".
    MicroServiceChoiceReplacementDic.objects.create(
        id="2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
        description="Yes",
        replacementdic='{"%AssignUUIDsToDirectories%": "True"}',
        choiceavailableatlink=dir_uuid_choice_chain_link,
        replaces_id=None,
    )

    ###########################################################################
    # Positioning
    ###########################################################################

    # Configure any links that exit to "Assign file UUIDs to objects" to now exit
    # to the "Assign UUIDs to directories?" choice link.
    MicroServiceChainLinkExitCode.objects.filter(
        nextmicroservicechainlink=assign_uuids_objects_chain_link
    ).update(nextmicroservicechainlink=dir_uuid_choice_chain_link)
    MicroServiceChainLink.objects.filter(
        defaultnextchainlink=assign_uuids_objects_chain_link
    ).exclude(id=dir_uuid_chain_link_uuid).update(
        defaultnextchainlink=dir_uuid_choice_chain_link
    )

    # Make "Assign UUIDs to directories" exit to "Assign file UUIDs to objects"
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("fb99fd16-516b-4db6-9789-39ad7f716a45", 0, 2),
        ("10d003a2-c6d1-4d0c-a2f5-8b30f0adbe90", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=dir_uuid_chain_link,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=assign_uuids_objects_chain_link,
        )

    # Make "Assign UUIDs to directories?" exit to "Assign UUIDs to directories"
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("76b2111a-754e-460a-ad99-22f98e2851b4", 0, 2),
        ("19bba699-0bf7-4778-8a2f-c7301285c833", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=dir_uuid_choice_chain_link,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=dir_uuid_chain_link,
        )

    # Make the "Set file permissions" chain link exit to the "Assign UUIDs to
    # directories?" link.
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink=assign_uuids_file_perm_chain_link
    ).update(nextmicroservicechainlink=dir_uuid_choice_chain_link)
    assign_uuids_file_perm_chain_link.defaultnextchainlink = dir_uuid_choice_chain_link


class Migration(migrations.Migration):

    dependencies = [("main", "0039_delete_sudo_clientscript")]

    operations = [
        # Modify the workflow:
        migrations.RunPython(data_migration),
        # Add the ``Directory`` model:
        migrations.CreateModel(
            name="Directory",
            fields=[
                (
                    "uuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="directoryUUID",
                    ),
                ),
                (
                    "originallocation",
                    main.models.BlobTextField(db_column="originalLocation"),
                ),
                (
                    "currentlocation",
                    main.models.BlobTextField(null=True, db_column="currentLocation"),
                ),
                (
                    "enteredsystem",
                    models.DateTimeField(auto_now_add=True, db_column="enteredSystem"),
                ),
                (
                    "sip",
                    models.ForeignKey(
                        db_column="sipUUID",
                        blank=True,
                        to="main.SIP",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "transfer",
                    models.ForeignKey(
                        db_column="transferUUID",
                        blank=True,
                        to="main.Transfer",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "Directories"},
        ),
        # Add the ``dirUUIDs`` field to the ``Transfer`` model:
        migrations.AddField(
            model_name="transfer",
            name="diruuids",
            field=models.BooleanField(default=False, db_column="dirUUIDs"),
        ),
    ]
