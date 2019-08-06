# -*- coding: utf-8 -*-
"""Migration for PID Binding: persistent identifier creation & resolution."""
from __future__ import absolute_import, print_function, unicode_literals

from django.db import migrations, models


def data_migration(apps, schema_editor):
    """Persistent Identifiers (PID) Workflow modifications (migration).
    This migration modifies the workflow so that there are three new
    micro-services, i.e., chain links, executed in the following order:

    1. Bind PIDs?, which asks the user whether to bind PIDs,
    2. Bind PID, which binds a PID to each file it is passed, and
    3. Bind PIDs, which binds PIDs to the entire unit and any directories (if
       directories have been given UUIDs.)

    These 3 new chain links are placed right before the "Generate METS.xml
    document" ("Generate AIP METS") link.

    Binding a PID means requesting from a Handle server a PID (a.k.a. a
    "handle") for a file, directory or unit, and requesting that the PID be
    set to resolve to a specific external URL. (Note that a desired
    PID---generally the UUID of the entity---is passed during handle creation.)
    That the PURL (i.e., PID's URL) may be configured to resolve to
    different external (resolve) URLs depending on the qualifier (GET query
    parameter) that is appended to it. See archivematicaCommon/lib/bindpid.py
    for more details.
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

    # This is the TaskType that handles client scripts that work on one file at
    # a time.
    each_file_task_type = TaskType.objects.get(description="for each file")

    # This is the TaskType that handles client scripts that treat an entire
    # directory (i.e., Transfer) in one go.
    entire_directory_task_type = TaskType.objects.get(description="one instance")

    # We need to position the two "Bind PIDs" chain links so that:
    # - "Verify checksums generated on ingest" comes before, and
    # - "Generate AIP METS" comes after.

    # Chain Link after is "Generate AIP METS"
    # Its UUID is ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0
    after_cl_uuid = "ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0"
    after_cl = MicroServiceChainLink.objects.get(id=after_cl_uuid)

    # Chain Link before is "Verify checksums generated on ingest"
    # Its UUID is 88807d68-062e-4d1a-a2d5-2d198c88d8ca
    before_cl_uuid = "88807d68-062e-4d1a-a2d5-2d198c88d8ca"
    before_cl = MicroServiceChainLink.objects.get(id=before_cl_uuid)

    ###########################################################################
    # New Chain Links: "Bind PIDs" - for whole unit: unit and dirs
    ###########################################################################

    # StandardTaskConfig that performs "Bind PIDs"
    bind_pids_stc_uuid = "0bd2524d-573a-4c8e-86b4-8fa54a5acfad"
    StandardTaskConfig.objects.create(
        id=bind_pids_stc_uuid,
        execute="bindPIDs_v0.0",
        arguments='"%SIPUUID%" "%sharedPath%" --bind-pids "%BindPIDs%"',
        stdout_file="%SIPLogsDirectory%handles.log",
    )

    # TaskConfig that performs "Bind PIDs"
    bind_pids_task_cfg_uuid = "88d8d473-6948-4f5d-abcb-12fb392df17a"
    bind_pids_task_cfg = TaskConfig.objects.create(
        id=bind_pids_task_cfg_uuid,
        tasktype=entire_directory_task_type,  # <= cp to ``each_file_task_type`` below
        description="Bind PIDs",
        tasktypepkreference=bind_pids_stc_uuid,
        replaces_id=None,
    )

    # MSChainLink that performs "Bind PIDs"
    bind_pids_chain_link_uuid = "7677d1cd-2211-4969-8c10-5ec2a93d5c2f"
    bind_pids_chain_link = MicroServiceChainLink.objects.create(
        id=bind_pids_chain_link_uuid,
        microservicegroup="Bind PIDs",
        defaultexitmessage="Failed",
        currenttask=bind_pids_task_cfg,
        replaces_id=None,
        # Comes before existing "Check if DIP should be generated" chain link.
        defaultnextchainlink=after_cl,
    )

    ###########################################################################
    # New Chain Links: "Bind PID" - for each file
    ###########################################################################

    # StandardTaskConfig that performs "Bind PID"
    bind_pid_stc_uuid = "b055f0a4-75d7-4747-98fe-aab08d835403"
    StandardTaskConfig.objects.create(
        id=bind_pid_stc_uuid,
        execute="bindPID_v0.0",
        arguments=('"%fileUUID%" --bind-pids "%BindPIDs%"'),
        stdout_file="%SIPLogsDirectory%handles.log",
    )

    # TaskConfig that performs "Bind PID"
    bind_pid_task_cfg_uuid = "9c9e75e9-04b0-4a04-83ad-07ddf2ff9a17"
    bind_pid_task_cfg = TaskConfig.objects.create(
        id=bind_pid_task_cfg_uuid,
        tasktype=each_file_task_type,
        description="Bind PID",
        tasktypepkreference=bind_pid_stc_uuid,
        replaces_id=None,
    )

    # MSChainLink that performs "Bind PID"
    bind_pid_chain_link_uuid = "87e93d08-36e4-4c81-99a8-beea00b18400"
    bind_pid_chain_link = MicroServiceChainLink.objects.create(
        id=bind_pid_chain_link_uuid,
        microservicegroup="Bind PIDs",
        defaultexitmessage="Failed",
        currenttask=bind_pid_task_cfg,
        replaces_id=None,
        # Comes before "Bind PIDs" chain link declared in stanza above.
        defaultnextchainlink=bind_pids_chain_link,
    )

    ###########################################################################
    # New Choice Chain Link: "Bind PIDs?"
    ###########################################################################

    # TaskConfig that asks "Bind PIDs?"
    bind_pids_choice_task_cfg_uuid = "02b44c99-f499-42d4-8742-3576c0d52804"
    bind_pids_choice_task_cfg = TaskConfig.objects.create(
        id=bind_pids_choice_task_cfg_uuid,
        tasktype=repl_dic_usr_choice_task_type,
        description="Bind PIDs?",
        tasktypepkreference=None,
        replaces_id=None,
    )

    # MSChainLink that asks "Bind PIDs?"
    bind_pids_choice_chain_link_uuid = "05357876-a095-4c11-86b5-a7fff01af668"
    bind_pids_choice_chain_link = MicroServiceChainLink.objects.create(
        id=bind_pids_choice_chain_link_uuid,
        microservicegroup="Bind PIDs",
        defaultexitmessage="Failed",
        currenttask=bind_pids_choice_task_cfg,
        replaces_id=None,
        # Comes before chain link created above
        defaultnextchainlink=bind_pid_chain_link,
    )

    # Create the "No" choice, i.e., "No, do not Bind PIDs".
    MicroServiceChoiceReplacementDic.objects.create(
        id="fcfea449-158c-452c-a8ad-4ae009c4eaba",
        description="No",
        replacementdic='{"%BindPIDs%": "False"}',
        choiceavailableatlink=bind_pids_choice_chain_link,
        replaces_id=None,
    )

    # Create the "Yes" choice, i.e., "Yes, do Bind PIDs".
    MicroServiceChoiceReplacementDic.objects.create(
        id="1e79e1b6-cf50-49ff-98a3-fa51d73553dc",
        description="Yes",
        replacementdic='{"%BindPIDs%": "True"}',
        choiceavailableatlink=bind_pids_choice_chain_link,
        replaces_id=None,
    )

    ###########################################################################
    # Positioning: Bind PIDs? < Bind PID < Bind PIDs
    ###########################################################################

    # Configure any links that exit to "Generate AIP METS" to
    # now exit to the "Bind PIDs?" choice link.
    MicroServiceChainLinkExitCode.objects.filter(
        nextmicroservicechainlink=after_cl
    ).update(nextmicroservicechainlink=bind_pids_choice_chain_link)
    MicroServiceChainLink.objects.filter(defaultnextchainlink=after_cl).exclude(
        id=bind_pids_chain_link_uuid
    ).update(defaultnextchainlink=bind_pids_choice_chain_link)

    # Make "Bind PIDs" exit to "Generate AIP METS"
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("ddb8ac64-b501-4350-aa51-f7ff5b0b70e5", 0, 2),
        ("6061da26-8a89-4656-9413-0a4420220656", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=bind_pids_chain_link,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=after_cl,
        )

    # Make "Bind PID" exit to "Bind PIDs"
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("5c20b218-76a9-4a59-aa47-96e8f0e8f2b0", 0, 2),
        ("556de3a0-1b8d-4fec-abbb-6b0608477869", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=bind_pid_chain_link,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=bind_pids_chain_link,
        )

    # Make "Bind PIDs?" exit to "Bind PID"
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
        ("6c23d182-30d4-4c39-a706-fe0fc0df6299", 0, 2),
        ("363319c1-eaf1-4bf7-ad34-1a38db4c7ca8", 1, 4),
    ):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=bind_pids_choice_chain_link,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=bind_pid_chain_link,
        )

    # Make the ``before`` chain link exit to the "Bind PIDs?" link.
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink=before_cl
    ).update(nextmicroservicechainlink=bind_pids_choice_chain_link)
    before_cl.defaultnextchainlink = bind_pids_choice_chain_link


class Migration(migrations.Migration):

    dependencies = [("main", "0040_directory_model")]

    operations = [
        # Modify the workflow:
        migrations.RunPython(data_migration),
        migrations.CreateModel(
            name="Identifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                ("type", models.TextField(null=True, verbose_name="Identifier Type")),
                (
                    "value",
                    models.TextField(
                        help_text="Used for premis:objectIdentifierType and premis:objectIdentifierValue in the METS file.",
                        null=True,
                        verbose_name="Identifier Value",
                    ),
                ),
            ],
            options={"db_table": "Identifiers"},
        ),
        migrations.AddField(
            model_name="directory",
            name="identifiers",
            field=models.ManyToManyField(to="main.Identifier"),
        ),
        migrations.AddField(
            model_name="sip",
            name="identifiers",
            field=models.ManyToManyField(to="main.Identifier"),
        ),
        migrations.AddField(
            model_name="file",
            name="identifiers",
            field=models.ManyToManyField(to="main.Identifier"),
        ),
        migrations.AddField(
            model_name="sip",
            name="diruuids",
            field=models.BooleanField(default=False, db_column="dirUUIDs"),
        ),
    ]
