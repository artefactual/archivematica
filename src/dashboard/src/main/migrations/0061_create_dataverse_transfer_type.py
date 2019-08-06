# -*- coding: utf-8 -*-
"""Migration to create a Dataverse Transfer Type.

This migration introduces a new transfer type for Dataverse,
https://dataverse.org/ datasets.

The migration also introduces two new microservices:

* Convert Dataverse Structure
* Parse Dataverse METS

In order to do that, the transfer workflow requires two signals in the form
of unit variables to read from when the new microservice tasks need to be
performed.

Once the tasks have completed, the workflow is picked up from where it would
normally for a standard transfer type.
"""
from __future__ import absolute_import, unicode_literals

from django.db import migrations

# We can't use apps.get_model for this model as we need to access class
# attributes.
from main.models import Job

# The usual default next MS in Archivematica is the failed transfer MS. The
# task that this points to is Email Fail Report.
DEFAULT_NEXT_MS_TASK_FAILED = "61c316a6-0a50-4f65-8767-1f44b1eeb6dd"

# Task types that we'll create entries for in this migration.
TASK_TYPE_LINK_PULL = "c42184a3-1a7f-4c4d-b380-15d8d97fdd11"
TASK_TYPE_SINGLE_INSTANCE = "36b2e239-4a57-4aa5-8ebc-7a29139baca6"
TASK_TYPE_SET_UNIT_VAR = "6f0b612c-867f-4dfd-8e43-5b35b7f882d7"
TASK_TYPE_USER_CHOICE = "61fb3874-8ef6-49d3-8a2d-3cb66e86a30c"

# New tasks created in this migration starting with user-choices.
NEW_CHOICE_TASK_APPROVE_DV_TRANSFER = "477bc37e-b6a7-440a-9088-85672b3b38a7"

# Tasks to set unit variables.
NEW_UNIT_VAR_TASK_CONVERT_DATAVERSE = "2b2042d4-548f-4c63-a394-bf14b5faa5d1"
NEW_UNIT_VAR_TASK_PARSE_DV_METS = "7d1872fc-d90e-4354-a5c9-97d24bbdf629"

# Standard task runners.
NEW_STD_TASK_SET_TRANSFER_TYPE_DV = "4d36c35a-0829-4b2d-ba3d-0a30a3e837f9"
NEW_STD_TASK_CONVERT_DATAVERSE = "ab6c6e52-10c5-449e-ae92-89cf7903e6bc"
NEW_STD_TASK_PARSE_DATAVERSE_METS = "e593507e-f4bf-4346-8652-32a832524782"

# New task configurations required to process a Dataverse transfer.
NEW_STD_TASK_CONFIG_SET_DV_TRANSFER = "ed3cda67-94b6-457e-9d00-c58f413dbfce"
NEW_STD_TASK_CONFIG_CONVERT_DV = "286b4b17-d382-48eb-bdbe-ca3b2a32568b"
NEW_STD_TASK_CONFIG_PARSE_DV = "58988b82-7b65-40f3-94a7-f2f3e13b8700"

# Configuration UUIDs for our Dataverse unit variables. These help determine
# the direction of the transfer workflow based on being able to identify a
# transfer as Dataverse.
NEW_UNIT_VAR_CONFIG_CONVERT_DV = "f5908626-38be-4c2b-9c09-a389585e9f6c"
NEW_UNIT_VAR_CONFIG_PARSE_DV = "3fcc6e42-0117-4786-9cd4-e773f6f71296"

# Tasks to make use of unit variables.
NEW_LINK_PULL_CONVERT_DATAVERSE = "7eade269-0bc3-4a6a-9801-e8e4d8babb55"
NEW_LINK_PULL_PARSE_DATAVERSE_METS = "355c22ae-ba5b-408b-a9b6-a01372d158b5"

# Configuration UUIDs for our Dataverse link pulls. These are used to direct
# the workflow based on previously set unit variables, if set.
NEW_LINK_PULL_CONFIG_CONVERT_DV = "5b11c0a9-6f62-4d7e-ad48-2905e75ff419"
NEW_LINK_PULL_CONFIG_PARSE_DV = "6f7a2ebd-bd88-44b7-b146-c552ac4e40cb"

# New chain choices to approve and reject a Dataverse transfer.
NEW_CHAIN_CHOICE_REJECT_DV_TRANSFER = "77bb4993-9f5b-4e60-bbe9-0039a6f5934e"
NEW_CHAIN_CHOICE_APPROVE_DV_TRANSFER = "dc9b59b3-dd5f-4cd6-8e97-ee1d83734c4c"

# New Microservices that we're creating.
NEW_MS_APPROVE_DV_TRANSFER = "246943e4-d203-48e1-ac84-4865520e7c30"
NEW_MS_MOVE_TO_PROCESSING_DIR = "fdb12ea6-22aa-46c8-a591-a2bcf5d42e5e"
NEW_MS_SET_DV_TRANSFER_TYPE = "0af6b163-5455-4a76-978b-e35cc9ee445f"
NEW_MS_SET_CONVERT_DV_UNIT_VAR = "213fe743-f170-4695-8b3e-77886a31a89d"
NEW_MS_SET_PARSE_DV_UNIT_VAR = "364ac694-6440-4e45-8b2a-d3715c524970"
NEW_MS_DETERMINE_CONVERT_DV = "2a0a7afb-d09b-414b-a7ae-625f162103c1"
NEW_MS_CONVERT_DV_STRUCTURE = "9ec31d55-f053-4695-b86d-8c2a8abdb0fc"
NEW_MS_DETERMINE_PARSE_DV = "ec3c965c-c056-47e3-a551-ad1966e00824"
NEW_MS_PARSE_DV_METS = "fba1fd92-150a-4969-84fb-f2c6097855cf"

# New Microservice Exit Codes that we want to create.
NEW_MS_EXIT_PROCESS_DIR_TO_DV_TRANSFER_TYPE = "f7e3753c-4df9-43fe-9c32-0d11c511308c"
NEW_MS_EXIT_SET_TTYPE_DV_TO_SET_CONV_DV = "da46e870-290b-4fd4-8f84-194b9177d8c0"
NEW_MS_EXIT_SET_CONV_DV_TO_SET_PARSE_DV = "4ce6a3bd-026b-4ce7-beae-809844bae289"
NEW_MS_EXIT_SET_PARSE_DV_TO_REMOVE_HIDDEN = "84647820-e56a-45cc-94a1-9f74de375ba8"
NEW_MS_EXIT_CONV_DV_TO_RESTRUCT_COMPLIANCE = "d515821d-b1f6-4ce9-b4e4-0503fa99c8cf"
NEW_MS_EXIT_PARSE_DV_PULL_TO_CREATE_METS = "5d37e917-f77b-44fa-b103-144a38722774"
NEW_MS_EXIT_PARSE_DV_TO_CREATE_METS = "d10e1118-4d6c-4d3c-a9a8-1307a2931a32"

# New microservice chains that we're creating.
NEW_MS_CHAIN_DV_IN_PROGRESS = "35a26b59-dcf3-45ec-b963-ba7bfaa8304f"
NEW_MS_CHAIN_APPROVE_DV_TRANSFER = "10c00bc8-8fc2-419f-b593-cf5518695186"

# New watched directories that we are creating.
NEW_WATCHED_DIR_DATAVERSE = "3901db52-dd1d-4b44-9d86-4285ddc5c022"

# Existing exit codes that we want to modify.
EXISTING_EXIT_CODE_UNNEEDED_TO_RESTRUCTURE = "9cb81a5c-a7a1-43a8-8eb6-3e999923e03c"
EXISTING_EXIT_CODE_VALIDATE_TO_POLICY = "434066e6-8205-4832-a71f-cc9cd8b539d2"

# Existing microservices that we want to reference, but eventually don't need
# to delete on migration down.
EXISTING_MS_REMOVE_HIDDEN = "50b67418-cb8d-434d-acc9-4a8324e7fdd2"
EXISTING_MS_REMOVE_UNNEEDED = "5d780c7d-39d0-4f4a-922b-9d1b0d217bca"
EXISTING_MS_RESTRUCTURE_COMPLIANCE = "ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c"
EXISTING_MS_VALIDATE_FORMATS = "a536828c-be65-4088-80bd-eb511a0a063d"
EXISTING_MS_POLICY_CHECKS = "70fc7040-d4fb-4d19-a0e6-792387ca1006"
EXISTING_MS_CREATE_TRANSFER_METS = "db99ab43-04d7-44ab-89ec-e09d7bbdc39d"

# Tasks that we want to reference, but eventually don't need to delete on
# migration down.
EXISTING_TASK_MOVE_TO_PROCESSING_DIR = "7c02a87b-7113-4851-97cd-2cf9d3fc0010"

# Chains that we want to reference, but eventually don't need to delete on
# migration down.
EXISTING_CHAIN_REJECT_TRANSFER = "1b04ec43-055c-43b7-9543-bd03c6a778ba"

# Watched directory type for transfers.
EXISTING_WATCHED_DIR_TYPE_TRANSFER = "f9a3a93b-f184-4048-8072-115ffac06b5d"

# Task and group names introduced in the Dataverse Transfer. Order is
# determined first by group, then description, and in the order which they
# appear in the workflow.
VERIFY_COMPLIANCE_GROUP = "Verify transfer compliance"
PARSE_EXTERNAL_FILES_GROUP = "Parse external files"
APPROVE_TRANSFER_DESC = "Approve Dataverse transfer"
SET_TRANSFER_TYPE_DESC = "Set transfer type: Dataverse"
TRANSFER_IN_PROGRESS_DESC = "Set Dataverse transfer in progress"
SET_CONVERT_DATAVERSE_DESC = "Set convert Dataverse structure flag"
SET_PARSE_DATAVERSE_DESC = "Set parse Dataverse METS flag"
CONVERT_DATAVERSE_DESC = "Convert Dataverse structure"
DETERMINE_CONVERSION_DESC = "Determine if Dataverse conversion needs to happen"
DETERMINE_PARSE_DATAVERSE_DESC = "Determine if Dataverse METS XML needs to be parsed"
PARSE_DATAVERSE_METS_DESC = "Parse Dataverse METS XML"


def create_variable_link_pull(apps, link_uuid, variable, default_ms_uuid=None):
    """Create a new variable link pull in the database."""
    apps.get_model("main", model_name="TaskConfigUnitVariableLinkPull").objects.create(
        id=link_uuid, variable=variable, defaultmicroservicechainlink_id=default_ms_uuid
    )


def create_set_unit_variable(
    apps, var_uuid, variable_name, variable_value=None, ms_uuid=None
):
    """Create a new unit variable in the database."""
    apps.get_model("main", model_name="TaskConfigSetUnitVariable").objects.create(
        id=var_uuid,
        variable=variable_name,
        variablevalue=variable_value,
        microservicechainlink_id=ms_uuid,
    )


def create_standard_task_config(apps, task_uuid, execute_string, args):
    """Create a task configuration, inc. the command and args and write to the
    database.
    """
    apps.get_model("main", model_name="StandardTaskConfig").objects.create(
        id=task_uuid, execute=execute_string, arguments=args
    )


def create_task(apps, task_type_uuid, task_uuid, task_desc, task_config=None):
    """Create a new task configuration entry in the database."""
    apps.get_model("main", model_name="TaskConfig").objects.create(
        id=task_uuid,
        description=task_desc,
        tasktype_id=task_type_uuid,
        tasktypepkreference=task_config,
    )


def create_ms_chain_link(
    apps,
    ms_uuid,
    group,
    task_uuid,
    ms_exit_message=Job.STATUS_FAILED,
    default_next_link=DEFAULT_NEXT_MS_TASK_FAILED,
):
    """Create a microservice chainlink in the database."""
    apps.get_model("main", model_name="MicroServiceChainLink").objects.create(
        id=ms_uuid,
        microservicegroup=group,
        defaultexitmessage=ms_exit_message,
        currenttask_id=task_uuid,
        defaultnextchainlink_id=default_next_link,
    )


def create_ms_chain(apps, chain_uuid, ms_uuid, chain_description):
    """Create a new chain in the database."""
    apps.get_model("main", model_name="MicroServiceChain").objects.create(
        id=chain_uuid, startinglink_id=ms_uuid, description=chain_description
    )


def create_ms_choice(apps, choice_uuid, chain_uuid, link_uuid):
    """Create a choice in the database."""
    apps.get_model("main", model_name="MicroServiceChainChoice").objects.create(
        id=choice_uuid, chainavailable_id=chain_uuid, choiceavailableatlink_id=link_uuid
    )


def create_watched_dir(apps, watched_uuid, dir_path, expected_type, chain_uuid):
    """Create a new watched directory in the database."""
    apps.get_model("main", model_name="WatchedDirectory").objects.create(
        id=watched_uuid,
        watched_directory_path=dir_path,
        expected_type_id=expected_type,
        chain_id=chain_uuid,
    )


def create_ms_exit_codes(
    apps,
    exit_code_uuid,
    ms_in,
    ms_out,
    ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY,
    update=False,
):
    """Create an exit code entry in the database."""
    if not update:
        apps.get_model(
            "main", model_name="MicroServiceChainLinkExitCode"
        ).objects.create(
            id=exit_code_uuid,
            microservicechainlink_id=ms_in,
            nextmicroservicechainlink_id=ms_out,
            exitmessage=ms_exit_message,
        )
        return
    apps.get_model("main", "MicroServiceChainLinkExitCode").objects.filter(
        id=exit_code_uuid
    ).update(nextmicroservicechainlink_id=ms_out)


def create_parse_dataverse_mets_link_pull(apps):
    """Enable Archivematica to detect that it needs to run the 'Parse Dataverse
    METS' microservice given a Dataverse transfer type.
    """

    # 355c22ae (Determine Parse Dataverse METS XML) task to associate with
    # a MicroServiceChainLink.
    create_task(
        apps=apps,
        task_type_uuid=TASK_TYPE_LINK_PULL,
        task_uuid=NEW_LINK_PULL_PARSE_DATAVERSE_METS,
        task_desc=DETERMINE_PARSE_DATAVERSE_DESC,
        task_config=NEW_LINK_PULL_CONFIG_PARSE_DV,
    )

    # ec3c965c (Determine Parse Dataverse METS XML).
    create_ms_chain_link(
        apps=apps,
        ms_uuid=NEW_MS_DETERMINE_PARSE_DV,
        group=PARSE_EXTERNAL_FILES_GROUP,
        task_uuid=NEW_LINK_PULL_PARSE_DATAVERSE_METS,
        ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY,
    )

    # If linkToParseDataverseMETS is set then goto the configured microservice,
    # else, goto the default microservice, 'Perform policy checks on
    # originals?'.
    create_variable_link_pull(
        apps=apps,
        link_uuid=NEW_LINK_PULL_CONFIG_PARSE_DV,
        variable="linkToParseDataverseMETS",
        default_ms_uuid=EXISTING_MS_POLICY_CHECKS,
    )

    # Break and Update the existing link to connect to our new link.
    # Original: 434066e6-8205-4832-a71f-cc9cd8b539d2
    # ms_1: a536828c-be65-4088-80bd-eb511a0a063d
    #       (Validate Formats)
    # ms_2: 70fc7040-d4fb-4d19-a0e6-792387ca1006
    #       (Perform policy checks on originals?)
    # New: 434066e6-8205-4832-a71f-cc9cd8b539d2
    # a536828c (Validate Formats)
    # ec3c965c (Determine Parse Dataverse METS XML)
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=EXISTING_EXIT_CODE_VALIDATE_TO_POLICY,
        ms_in=EXISTING_MS_VALIDATE_FORMATS,
        ms_out=NEW_MS_DETERMINE_PARSE_DV,
        update=True,
    )

    # Create a new link now we have broken the original.
    # ec3c965c (Determine Parse Dataverse METS XML)
    # db99ab43 (Create transfer metadata XML)
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=NEW_MS_EXIT_PARSE_DV_PULL_TO_CREATE_METS,
        ms_in=NEW_MS_DETERMINE_PARSE_DV,
        ms_out=EXISTING_MS_CREATE_TRANSFER_METS,
    )


def create_convert_dataverse_link_pull(apps):
    """Enable Archivematica to detect that it needs to run the 'Convert
    Dataverse Structure' microservice given a Dataverse transfer type.
    """

    # 7eade269 (Determine Dataverse Conversion) task to associate with
    # a MicroServiceChainLink.
    create_task(
        apps=apps,
        task_type_uuid=TASK_TYPE_LINK_PULL,
        task_uuid=NEW_LINK_PULL_CONVERT_DATAVERSE,
        task_desc=DETERMINE_CONVERSION_DESC,
        task_config=NEW_LINK_PULL_CONFIG_CONVERT_DV,
    )

    # 7eade269 (Determine Dataverse Conversion).
    create_ms_chain_link(
        apps=apps,
        ms_uuid=NEW_MS_DETERMINE_CONVERT_DV,
        group=VERIFY_COMPLIANCE_GROUP,
        task_uuid=NEW_LINK_PULL_CONVERT_DATAVERSE,
        ms_exit_message=Job.STATUS_COMPLETED_SUCCESSFULLY,
    )

    # If linkToConvertDataverseStructure is set then goto the configured
    # microservice, else, goto the default microservice.
    create_variable_link_pull(
        apps=apps,
        link_uuid=NEW_LINK_PULL_CONFIG_CONVERT_DV,
        variable="linkToConvertDataverseStructure",
        default_ms_uuid=EXISTING_MS_RESTRUCTURE_COMPLIANCE,
    )

    # Break and Update the existing link to connect to our new link.
    # Original: 9cb81a5c-a7a1-43a8-8eb6-3e999923e03c
    # ms_1: 5d780c7d-39d0-4f4a-922b-9d1b0d217bca
    #       (Remove unneeded files)
    # ms_2: ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c
    #       (Attempt restructure for compliance)
    # New: 9cb81a5c-a7a1-43a8-8eb6-3e999923e03c
    # 5d780c7d (Remove Unneeded Files) connects to:
    # 2a0a7afb (Determine Dataverse Conversion)
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=EXISTING_EXIT_CODE_UNNEEDED_TO_RESTRUCTURE,
        ms_in=EXISTING_MS_REMOVE_UNNEEDED,
        ms_out=NEW_MS_DETERMINE_CONVERT_DV,
        update=True,
    )

    # Create a new link now we have broken the original.
    # 9ec31d55 (Convert Dataverse Structure) connects to:
    # ea0e8838 (Attempt Restructure For Compliance)
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=NEW_MS_EXIT_CONV_DV_TO_RESTRUCT_COMPLIANCE,
        ms_in=NEW_MS_CONVERT_DV_STRUCTURE,
        ms_out=EXISTING_MS_RESTRUCTURE_COMPLIANCE,
    )


def create_parse_dataverse_mets_microservice(apps):
    """Create the database rows specific to the parse Dataverse METS
    microservice.
    """

    # Pointer to the parse Dataverse client script.
    create_standard_task_config(
        apps=apps,
        task_uuid=NEW_STD_TASK_CONFIG_PARSE_DV,
        execute_string="parseDataverse_v0.0",
        args="%SIPDirectory% %SIPUUID%",
    )

    # e593507e (Parse Dataverse METS XML) task to be associated with a
    # MicroServiceChainLink.
    create_task(
        apps=apps,
        task_type_uuid=TASK_TYPE_SINGLE_INSTANCE,
        task_uuid=NEW_STD_TASK_PARSE_DATAVERSE_METS,
        task_desc=PARSE_DATAVERSE_METS_DESC,
        task_config=NEW_STD_TASK_CONFIG_PARSE_DV,
    )

    # fba1fd92 (Parse Dataverse METS XML) Chainlink.
    create_ms_chain_link(
        apps=apps,
        ms_uuid=NEW_MS_PARSE_DV_METS,
        group=PARSE_EXTERNAL_FILES_GROUP,
        task_uuid=NEW_STD_TASK_PARSE_DATAVERSE_METS,
    )

    # Create a new link now we have broken the original.
    # fba1fd92 (Parse Dataverse METS XML) connects to:
    # db99ab43 (Create transfer metadata XML)
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=NEW_MS_EXIT_PARSE_DV_TO_CREATE_METS,
        ms_in=NEW_MS_PARSE_DV_METS,
        ms_out=EXISTING_MS_CREATE_TRANSFER_METS,
    )


def create_dataverse_unit_variables_and_initial_tasks(apps):
    """Once the Dataverse transfer has started then the Archivematica
    workflow needs to know how to route itself. We set two unit variables
    here which are used later in the workflow, and we set the first Dataverse
    specific microservice to run, 'Convert Dataverse Structure'
    """

    # Create a Task that creates a unit variable to instruct Archivematica to
    # convert a Dataverse metadata structure to METS.
    create_task(
        apps=apps,
        task_type_uuid=TASK_TYPE_SET_UNIT_VAR,
        task_uuid=NEW_UNIT_VAR_TASK_CONVERT_DATAVERSE,
        task_desc=SET_CONVERT_DATAVERSE_DESC,
        task_config=NEW_UNIT_VAR_CONFIG_CONVERT_DV,
    )

    # Create a Task that creates a unit variable to instruct Archivematica to
    # process an external Dataverse METS.
    create_task(
        apps=apps,
        task_type_uuid=TASK_TYPE_SET_UNIT_VAR,
        task_uuid=NEW_UNIT_VAR_TASK_PARSE_DV_METS,
        task_desc=SET_PARSE_DATAVERSE_DESC,
        task_config=NEW_UNIT_VAR_CONFIG_PARSE_DV,
    )

    # Create a MicroServiceChainLink to point to the 'Set Dataverse Transfer'
    # Create Unit Variable Task.
    create_ms_chain_link(
        apps=apps,
        ms_uuid=NEW_MS_SET_CONVERT_DV_UNIT_VAR,
        group=VERIFY_COMPLIANCE_GROUP,
        task_uuid=NEW_UNIT_VAR_TASK_CONVERT_DATAVERSE,
    )

    # Create a MicroServiceChainLink to point to the 'Set Parse Dataverse METS'
    # Create Unit Variable Task.
    create_ms_chain_link(
        apps=apps,
        ms_uuid=NEW_MS_SET_PARSE_DV_UNIT_VAR,
        group=VERIFY_COMPLIANCE_GROUP,
        task_uuid=NEW_UNIT_VAR_TASK_PARSE_DV_METS,
    )

    # Create the MicroServiceChainLinks required to ask Archivematica to
    # process a transfer as a Dataverse one.

    # Pointer to the convert Dataverse structure MCP Client script.
    create_standard_task_config(
        apps=apps,
        task_uuid=NEW_STD_TASK_CONFIG_CONVERT_DV,
        execute_string="convertDataverseStructure_v0.0",
        args="%SIPDirectory%",
    )

    # ab6c6e52 (Convert Dataverse Structure) task to be associated with a
    # MicroServiceChainLink.
    create_task(
        apps=apps,
        task_type_uuid=TASK_TYPE_SINGLE_INSTANCE,
        task_uuid=NEW_STD_TASK_CONVERT_DATAVERSE,
        task_desc=CONVERT_DATAVERSE_DESC,
        task_config=NEW_STD_TASK_CONFIG_CONVERT_DV,
    )

    # ab6c6e52 (Convert Dataverse Structure) Chainlink.
    create_ms_chain_link(
        apps=apps,
        ms_uuid=NEW_MS_CONVERT_DV_STRUCTURE,
        group=VERIFY_COMPLIANCE_GROUP,
        task_uuid=NEW_STD_TASK_CONVERT_DATAVERSE,
    )

    # Create a set of unit variables to enable Archivematica to see this as a
    # Dataverse transfer and process the contents downloaded via the Storage
    # Service appropriately.
    create_set_unit_variable(
        apps=apps,
        var_uuid=NEW_UNIT_VAR_CONFIG_CONVERT_DV,
        variable_name="linkToConvertDataverseStructure",
        ms_uuid=NEW_MS_CONVERT_DV_STRUCTURE,
    )

    # Create a unit variable to determine that the external METS file created
    # for Dataverse will be parsed later on in the process by Archivematica.
    create_set_unit_variable(
        apps=apps,
        var_uuid=NEW_UNIT_VAR_CONFIG_PARSE_DV,
        variable_name="linkToParseDataverseMETS",
        ms_uuid=NEW_MS_PARSE_DV_METS,
    )

    # Break and Update the existing link to connect to our new link.
    # 0af6b163 (Set Transfer Type: Dataverse) connects to:
    # 213fe743 (Set Convert Dataverse Structure (Unit Variable))
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=NEW_MS_EXIT_SET_TTYPE_DV_TO_SET_CONV_DV,
        ms_in=NEW_MS_SET_DV_TRANSFER_TYPE,
        ms_out=NEW_MS_SET_CONVERT_DV_UNIT_VAR,
        update=True,
    )

    # Create a new link now we have broken the original.
    # 213fe743 (Set Convert Dataverse Structure) connects to:
    # 364ac694 (Set Parse Dataverse METS (Unit Variable))
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=NEW_MS_EXIT_SET_CONV_DV_TO_SET_PARSE_DV,
        ms_in=NEW_MS_SET_CONVERT_DV_UNIT_VAR,
        ms_out=NEW_MS_SET_PARSE_DV_UNIT_VAR,
    )

    # Create a new link now we have broken the original.
    # 364ac694 (Set Parse Dataverse (Unit Variable)) connects to:
    # 50b67418 (Remove hidden files and directories).
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=NEW_MS_EXIT_SET_PARSE_DV_TO_REMOVE_HIDDEN,
        ms_in=NEW_MS_SET_PARSE_DV_UNIT_VAR,
        ms_out=EXISTING_MS_REMOVE_HIDDEN,
    )


def create_dataverse_transfer_type(apps):
    """Create the database rows required to create a new transfer type in
    Archivematica.
    """

    # Configuration of transfer initiation tasks.
    create_standard_task_config(
        apps=apps,
        task_uuid=NEW_STD_TASK_CONFIG_SET_DV_TRANSFER,
        execute_string="archivematicaSetTransferType_v0.0",
        args='"%SIPUUID%" "Dataverse"',
    )

    # Create tasks related to the initiation of a new Dataverse transfer.
    create_task(
        apps=apps,
        task_type_uuid=TASK_TYPE_USER_CHOICE,
        task_uuid=NEW_CHOICE_TASK_APPROVE_DV_TRANSFER,
        task_desc=APPROVE_TRANSFER_DESC,
    )
    create_task(
        apps=apps,
        task_type_uuid=TASK_TYPE_SINGLE_INSTANCE,
        task_uuid=NEW_STD_TASK_SET_TRANSFER_TYPE_DV,
        task_desc=SET_TRANSFER_TYPE_DESC,
        task_config=NEW_STD_TASK_CONFIG_SET_DV_TRANSFER,
    )

    # 246943e4 (Approve Dataverse transfer)
    create_ms_chain_link(
        apps=apps,
        ms_uuid=NEW_MS_APPROVE_DV_TRANSFER,
        group=APPROVE_TRANSFER_DESC,
        task_uuid=NEW_CHOICE_TASK_APPROVE_DV_TRANSFER,
    )

    # fdb12ea6 (Move to processing directory)
    create_ms_chain_link(
        apps=apps,
        ms_uuid=NEW_MS_MOVE_TO_PROCESSING_DIR,
        group=VERIFY_COMPLIANCE_GROUP,
        task_uuid=EXISTING_TASK_MOVE_TO_PROCESSING_DIR,
    )

    # 0af6b163 (Set transfer type: Dataverse)
    create_ms_chain_link(
        apps=apps,
        ms_uuid=NEW_MS_SET_DV_TRANSFER_TYPE,
        group=VERIFY_COMPLIANCE_GROUP,
        task_uuid=NEW_STD_TASK_SET_TRANSFER_TYPE_DV,
    )

    # Create chains for the initiation of Dataverse transfers.
    create_ms_chain(
        apps=apps,
        chain_uuid=NEW_MS_CHAIN_DV_IN_PROGRESS,
        ms_uuid=NEW_MS_APPROVE_DV_TRANSFER,
        chain_description=TRANSFER_IN_PROGRESS_DESC,
    )
    create_ms_chain(
        apps=apps,
        chain_uuid=NEW_MS_CHAIN_APPROVE_DV_TRANSFER,
        ms_uuid=NEW_MS_MOVE_TO_PROCESSING_DIR,
        chain_description=APPROVE_TRANSFER_DESC,
    )

    # Approve Dataverse transfer
    create_ms_choice(
        apps=apps,
        choice_uuid=NEW_CHAIN_CHOICE_APPROVE_DV_TRANSFER,
        chain_uuid=NEW_MS_CHAIN_APPROVE_DV_TRANSFER,
        link_uuid=NEW_MS_APPROVE_DV_TRANSFER,
    )

    # Reject Dataverse transfer
    create_ms_choice(
        apps=apps,
        choice_uuid=NEW_CHAIN_CHOICE_REJECT_DV_TRANSFER,
        chain_uuid=EXISTING_CHAIN_REJECT_TRANSFER,
        link_uuid=NEW_MS_APPROVE_DV_TRANSFER,
    )

    # Create a watched directory which will be where transfers can be
    # initiated.
    create_watched_dir(
        apps=apps,
        watched_uuid=NEW_WATCHED_DIR_DATAVERSE,
        dir_path="%watchDirectoryPath%activeTransfers/dataverseTransfer",
        expected_type=EXISTING_WATCHED_DIR_TYPE_TRANSFER,
        chain_uuid=NEW_MS_CHAIN_DV_IN_PROGRESS,
    )

    # Create a new link now we have broken the original.
    # fdb12ea6 (Move to processing directory) connects to:
    # 0af6b163 (Set transfer type: Dataverse)
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=NEW_MS_EXIT_PROCESS_DIR_TO_DV_TRANSFER_TYPE,
        ms_in=NEW_MS_MOVE_TO_PROCESSING_DIR,
        ms_out=NEW_MS_SET_DV_TRANSFER_TYPE,
    )

    # Create a new link now we have broken the original.
    # 0af6b163 (Set transfer type: Dataverse) connects to:
    # 50b67418 (Remove hidden files and directories)
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=NEW_MS_EXIT_SET_TTYPE_DV_TO_SET_CONV_DV,
        ms_in=NEW_MS_SET_DV_TRANSFER_TYPE,
        ms_out=EXISTING_MS_REMOVE_HIDDEN,
    )


def data_migration_up(apps, schema_editor):
    """Run the various groupings of migration functions for the Dataverse
    specific transfer type.
    """
    create_dataverse_transfer_type(apps)
    create_parse_dataverse_mets_microservice(apps)
    create_dataverse_unit_variables_and_initial_tasks(apps)
    create_convert_dataverse_link_pull(apps)
    create_parse_dataverse_mets_link_pull(apps)


def data_migration_down(apps, schema_editor):
    """Reverse the changes made to the database in order to create a Dataverse
    transfer type.
    """

    # Fix the originally broken chain links:
    # Original: 9cb81a5c-a7a1-43a8-8eb6-3e999923e03c
    # ms_1: 5d780c7d-39d0-4f4a-922b-9d1b0d217bca
    #       (Remove unneeded files)
    # ms_2: ea0e8838-ad3a-4bdd-be14-e5dba5a4ae0c
    #       (Attempt restructure for compliance)
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=EXISTING_EXIT_CODE_UNNEEDED_TO_RESTRUCTURE,
        ms_in=EXISTING_MS_REMOVE_UNNEEDED,
        ms_out=EXISTING_MS_RESTRUCTURE_COMPLIANCE,
        update=True,
    )

    # Original: 434066e6-8205-4832-a71f-cc9cd8b539d2
    # ms_1: a536828c-be65-4088-80bd-eb511a0a063d
    #       (Validate Formats)
    # ms_2: 70fc7040-d4fb-4d19-a0e6-792387ca1006
    #       (Perform policy checks on originals?)
    create_ms_exit_codes(
        apps=apps,
        exit_code_uuid=EXISTING_EXIT_CODE_VALIDATE_TO_POLICY,
        ms_in=EXISTING_MS_VALIDATE_FORMATS,
        ms_out=EXISTING_MS_POLICY_CHECKS,
        update=True,
    )

    # Once we've fixed the previous chains, we can delete the extraneous pieces
    # introduced by the attempt to create the transfer type here.

    # Remove WatchedDirectories
    apps.get_model("main", model_name="WatchedDirectory").objects.filter(
        id=NEW_WATCHED_DIR_DATAVERSE
    ).delete()

    # Remove MicroServiceChains
    for uuid_ in [NEW_MS_CHAIN_APPROVE_DV_TRANSFER, NEW_MS_CHAIN_DV_IN_PROGRESS]:
        apps.get_model("main", model_name="MicroServiceChain").objects.filter(
            id=uuid_
        ).delete()

    # Remove MicroServiceExitCodes
    for uuid_ in [
        NEW_MS_EXIT_SET_TTYPE_DV_TO_SET_CONV_DV,
        NEW_MS_EXIT_SET_CONV_DV_TO_SET_PARSE_DV,
        NEW_MS_EXIT_SET_PARSE_DV_TO_REMOVE_HIDDEN,
        NEW_MS_EXIT_CONV_DV_TO_RESTRUCT_COMPLIANCE,
        NEW_MS_EXIT_PROCESS_DIR_TO_DV_TRANSFER_TYPE,
        NEW_MS_EXIT_PARSE_DV_TO_CREATE_METS,
        NEW_MS_EXIT_PARSE_DV_PULL_TO_CREATE_METS,
    ]:
        apps.get_model(
            "main", model_name="MicroServiceChainLinkExitCode"
        ).objects.filter(id=uuid_).delete()

    # Remove MicroServiceChainLinks
    for uuid_ in [
        NEW_MS_APPROVE_DV_TRANSFER,
        NEW_MS_SET_DV_TRANSFER_TYPE,
        NEW_MS_MOVE_TO_PROCESSING_DIR,
        NEW_MS_SET_CONVERT_DV_UNIT_VAR,
        NEW_MS_SET_PARSE_DV_UNIT_VAR,
        NEW_MS_DETERMINE_CONVERT_DV,
        NEW_MS_CONVERT_DV_STRUCTURE,
        NEW_MS_DETERMINE_PARSE_DV,
        NEW_MS_PARSE_DV_METS,
    ]:
        apps.get_model("main", model_name="MicroServiceChainLink").objects.filter(
            id=uuid_
        ).delete()

    # Remove MicroServiceChain Choices
    for uuid_ in [
        NEW_CHAIN_CHOICE_APPROVE_DV_TRANSFER,
        NEW_CHAIN_CHOICE_REJECT_DV_TRANSFER,
    ]:
        apps.get_model("main", model_name="MicroServiceChainChoice").objects.filter(
            id=uuid_
        ).delete()

    # Remove Standard Task Configurations
    for uuid_ in [
        NEW_STD_TASK_CONFIG_SET_DV_TRANSFER,
        NEW_STD_TASK_CONFIG_CONVERT_DV,
        NEW_STD_TASK_CONFIG_PARSE_DV,
    ]:
        apps.get_model("main", model_name="StandardTaskConfig").objects.filter(
            id=uuid_
        ).delete()

    # Remove Task Configurations
    for uuid_ in [
        NEW_UNIT_VAR_TASK_CONVERT_DATAVERSE,
        NEW_UNIT_VAR_TASK_PARSE_DV_METS,
        NEW_STD_TASK_CONVERT_DATAVERSE,
        NEW_LINK_PULL_CONVERT_DATAVERSE,
        NEW_CHOICE_TASK_APPROVE_DV_TRANSFER,
        NEW_STD_TASK_SET_TRANSFER_TYPE_DV,
        NEW_STD_TASK_PARSE_DATAVERSE_METS,
        NEW_LINK_PULL_PARSE_DATAVERSE_METS,
    ]:
        apps.get_model("main", model_name="TaskConfig").objects.filter(
            id=uuid_
        ).delete()

    # Remove Set Unit Variables
    for uuid_ in [NEW_UNIT_VAR_CONFIG_CONVERT_DV, NEW_UNIT_VAR_CONFIG_PARSE_DV]:
        apps.get_model("main", model_name="TaskConfigSetUnitVariable").objects.filter(
            id=uuid_
        ).delete()

    # Remove Variable Link Pulls
    for uuid_ in [NEW_LINK_PULL_CONFIG_CONVERT_DV, NEW_LINK_PULL_CONFIG_PARSE_DV]:
        apps.get_model(
            "main", model_name="TaskConfigUnitVariableLinkPull"
        ).objects.filter(id=uuid_).delete()


class Migration(migrations.Migration):
    """Run the migration to create a Dataverse Transfer Type."""

    dependencies = [("main", "0060_delete_orphan_mscl")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
