# -*- coding: utf-8 -*-
"""Helper functions for migrations writing new Microservice chainlinks to the
Archivematica database.
"""
from __future__ import unicode_literals

import json
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel("INFO")

# Default failure path for all Microservice links.
MS_EXIT_MESSAGE = "Failed"
DEFAULT_NEXT_MS = "61c316a6-0a50-4f65-8767-1f44b1eeb6dd"

# Default values for all Microservice Exit Codes.
MS_EXIT_CODE = 0
MS_COMPLETED_SUCCESSFULLY = 2


def read_standard_task_config(apps, schema_editor, standard_task):
    """Read and create a command entry for a standard task type."""
    task_uuid = standard_task.get("task_uuid")
    execute_string = standard_task.get("execute_string")
    args = standard_task.get("args")

    logger.info("Creating task config entry: %s", task_uuid)

    create_standard_task(apps,
                         schema_editor,
                         task_uuid=task_uuid,
                         execute_string=execute_string,
                         args=args)


def read_variable_link_pull(apps, schema_editor, variable_link):
    """Read the variable link pull fields and update the database."""
    link_uuid = variable_link.get("link_uuid")
    variable = variable_link.get("variable")
    ms_uuid = variable_link.get("default_next_link")
    task_link_back = variable_link.get("task_link_back")

    logger.info("Creating variable link pull: %s", link_uuid)

    create_variable_link_pull(
        apps,
        schema_editor,
        link_uuid=link_uuid,
        variable=variable,
        ms_uuid=ms_uuid,
    )

    logger.info("Updating task: %s", task_link_back)

    update_task(
        apps,
        schema_editor,
        task_uuid=task_link_back,
        task_config=link_uuid,
    )


def read_task(apps, schema_editor, task, create_config=True):
    """Read and create a task configuration entry for a task.

    We will write the task configuration only if we can satisfy the foreign
    key constraints. If create_config is set to False, we will write None
    initially.

    We will loop through the tasks again later and then update the config when
    we have one available.
    """
    task_type_uuid = task.get("task_type_uuid")
    task_uuid = task.get("task_uuid")
    task_desc = task.get("task_description")

    if create_config:
        task_config = task.get("task_config")
    else:
        task_config = None

    logger.info("Creating task: %s", task_desc)

    create_task(apps,
                schema_editor,
                task_type_uuid=task_type_uuid,
                task_uuid=task_uuid,
                task_desc=task_desc,
                task_config=task_config)


def read_ms(apps, schema_editor, microservice):
    ms_uuid = microservice.get("ms_in_uuid")
    group = microservice.get("group")
    exit_msg = microservice.get("default_exit_message", MS_EXIT_MESSAGE)
    task_id = microservice.get("task_uuid")
    default_next_chainlink = microservice.get("default_next_ms", DEFAULT_NEXT_MS)

    # An exit code entry can sometimes make use of the same microservice
    # chainlink and determines what happens next based on its exit code. To
    # mitigate creating a chainlink twice in this code, we set a flag called
    # ms_duplicate.

    ms_duplicate = microservice.get("ms_duplicate", False)

    logger.info("Creating chain link: %s", ms_uuid)

    if not ms_duplicate:
        create_ms_chain_link(apps,
                             schema_editor,
                             ms_uuid=ms_uuid,
                             group=group,
                             task_uuid=task_id,
                             ms_exit_message=exit_msg,
                             default_next_link=default_next_chainlink)


def read_ms_chain(apps, schema_editor, chain):
    """Read the chain information and create the chain entry in the DB."""
    chain_uuid = chain.get("chain_uuid")
    starting_link = chain.get("ms_uuid")
    description = chain.get("description")

    logger.info("Creating chain: %s", chain_uuid)

    create_ms_chain(apps,
                    schema_editor,
                    chain_uuid=chain_uuid,
                    ms_uuid=starting_link,
                    chain_description=description,
                    )


def read_watched(apps, schema_editor, watched):
    """Read the watched directories we need to create."""
    path = watched.get("path")
    dir_id = watched.get("dir_id")
    type_ = watched.get("dir_type")
    chain = watched.get("chain")

    logger.info("Creating watched directory %s", dir_id)

    create_watched_dir(apps,
                       schema_editor,
                       watched_uuid=dir_id,
                       dir_path=path,
                       expected_type=type_,
                       chain_uuid=chain,
                       )


def read_choice(apps, schema_editor, microservice):
    """Read choices available to a particular microservice."""
    choices = microservice.get("choice")
    if choices is not None:
        for choice in choices:
            choice_uuid = choice.get("id")
            chain_uuid = choice.get("chain_uuid")
            ms_uuid = choice.get("at_link_uuid")
            logger.info("Creating choice %s", choice_uuid)
            create_ms_choice(apps,
                             schema_editor,
                             choice_uuid=choice_uuid,
                             chain_uuid=chain_uuid,
                             link_uuid=ms_uuid,
                             )


def read_dict_choice(apps, schema_editor, microservice):
    """Read dictionary based choices in a particular microservice."""
    choices = microservice.get("dict_choice")
    if choices is not None:
        for choice in choices:
            choice_uuid = choice.get("id")
            at_link_uuid = choice.get("at_link_uuid")
            description = choice.get("description")
            replacement_dict = choice.get("replacement_dict")
            logger.info("Creating dict choice: %s", choice_uuid)
            create_ms_dict_choice(apps,
                                  schema_editor,
                                  choice_uuid=choice_uuid,
                                  desc=description,
                                  replacement_dict=replacement_dict,
                                  link_uuid=at_link_uuid)


def read_ms_exitcode(apps, schema_editor, microservice):
    """Read the microservice exit codes and connect them together."""
    exit_uuid = microservice.get("exit_uuid")
    ms_in_id = microservice.get("ms_in_uuid")
    ms_out_id = microservice.get("ms_out_uuid")

    exit_code = microservice.get("exit_code", MS_EXIT_CODE)
    exit_message = microservice.get("exit_message", MS_COMPLETED_SUCCESSFULLY)

    logger.info("Connecting %s to %s", ms_in_id, ms_out_id)

    if exit_uuid is not None:
        create_ms_exit_codes(apps,
                             schema_editor,
                             exit_code_uuid=exit_uuid,
                             ms_in=ms_in_id,
                             ms_out=ms_out_id,
                             ms_exit_code=exit_code,
                             ms_exit_message=exit_message
                             )


def read_json_links(apps, schema_editor, json_data):
    """read_json_links

    To create a new workflow you need to follow a certain order which goes:
    * Tasks
    * Chain Links
    * Chains
    * Watched Directories
    * Choices

    Each step relies on the previous where public-keys often need to exist
    for another database entity that you are referring to. For example, a
    chain cannot begin without a chainlink. A chainlink cannot exist without
    a task, and so forth.

    We cycle through a JSON workflow specification here and create each piece
    as we go.
    """
    ttype = json_data.get('transfer_type')
    if ttype:
        standard_tasks_config = ttype.get("standard_task_config", [])
        for standard in standard_tasks_config:
            read_standard_task_config(apps, schema_editor, standard)
        tasks = ttype.get('tasks', [])
        for task in tasks:
            type_ = task.get("task_type_uuid")
            if type_ == "c42184a3-1a7f-4c4d-b380-15d8d97fdd11":
                read_task(apps, schema_editor, task, create_config=False)
            else:
                read_task(apps, schema_editor, task)
        links = ttype.get('microservices', [])
        for link in links:
            read_ms(apps, schema_editor, link)
        variable_link = ttype.get("variable_link_pull", [])
        for link in variable_link:
            read_variable_link_pull(apps, schema_editor, link)
        chains = ttype.get("chains", [])
        for chain in chains:
            read_ms_chain(apps, schema_editor, chain)
        watched_dirs = ttype.get("watched_dirs", [])
        for watched in watched_dirs:
            read_watched(apps, schema_editor, watched)
        # Because choices refer specifically to a chain link, we can reuse the
        # links variable here and cycle through those instead.
        for choice in links:
            read_choice(apps, schema_editor, choice)
        for dict_choice in links:
            read_dict_choice(apps, schema_editor, dict_choice)
        for exit_codes in links:
            read_ms_exitcode(apps, schema_editor, exit_codes)
    return


def read_json(fname):
    """Read a workflow file into a dict and return to the calling function."""
    with open(fname, 'r') as json_data_file:
        data = json.load(json_data_file)
        return data


def create_standard_task(apps, schema_editor, task_uuid, execute_string, args):
    """Create a task configuration, inc. the command and args and write to the
    database.
    """
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    StandardTaskConfig.objects.create(
        id=task_uuid,
        requires_output_lock=0,
        execute=execute_string,
        arguments=args,
    )


def create_variable_link_pull(
        apps, schema_editor, link_uuid, variable, ms_uuid):
    """Create a new variable link pull in the database."""
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "TaskConfigUnitVariableLinkPull"
    )
    MicroServiceChainLinkExitCode.objects.create(
        id=link_uuid,
        variable=variable,
        defaultmicroservicechainlink=get_ms_chain_link_instance(
            apps,
            schema_editor,
            ms_uuid=ms_uuid,
        )
    )


def create_task(
        apps, schema_editor,
        task_type_uuid, task_uuid, task_desc, task_config):
    """Create a new task configuration entry in the database."""
    get_task_type = get_task_type_instance(
        apps,
        schema_editor,
        task_type_uuid
    )
    tasks_config_table = apps.get_model('main', 'TaskConfig')
    tasks_config_table.objects.create(
        id=task_uuid,
        description=task_desc,
        tasktype=get_task_type,
        tasktypepkreference=task_config,
    )


def update_task(apps, schema_editor, task_uuid, task_config):
    """Update the task config table when we have all the info needed."""
    tasks_config_table = apps.get_model('main', 'TaskConfig')
    tasks_config_table.objects.filter(
        id=task_uuid
    ).update(tasktypepkreference=task_config)


def create_ms_chain_link(
        apps, schema_editor, ms_uuid, group, task_uuid,
        ms_exit_message=MS_EXIT_MESSAGE, default_next_link=DEFAULT_NEXT_MS):
    """Create a microservice chainlink in the database."""
    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChainLink.objects.create(
        id=ms_uuid,
        microservicegroup=group,
        defaultexitmessage=ms_exit_message,
        currenttask_id=task_uuid,
        defaultnextchainlink_id=default_next_link,
    )


def create_ms_chain(
        apps, schema_editor, chain_uuid, ms_uuid, chain_description):
    """Create a new chain in the database."""
    ms_chain_link = get_ms_chain_link_instance(
        apps,
        schema_editor,
        ms_uuid=ms_uuid
    )
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChain.objects.create(
        id=chain_uuid,
        startinglink=ms_chain_link,
        description=chain_description,
    )


def create_watched_dir(
        apps, schema_editor, watched_uuid,
        dir_path, expected_type, chain_uuid):
    """Create a new watched directory in the database."""
    only_act_on_dirs = 1
    watched_directory_model = apps.get_model('main', 'WatchedDirectory')
    watched_directory_model.objects.create(
        id=watched_uuid,
        watched_directory_path=dir_path,
        only_act_on_directories=only_act_on_dirs,
        expected_type=get_watched_type_instance(
            apps,
            schema_editor,
            type_uuid=expected_type
        ),
        chain=get_ms_chain_instance(
            apps,
            schema_editor,
            chain_uuid=chain_uuid
        ),
    )


def create_ms_choice(apps, schema_editor, choice_uuid, chain_uuid, link_uuid):
    """Create a choice in the database."""
    microservice_chain_choice_table = apps\
        .get_model('main', 'MicroServiceChainChoice')
    microservice_chain_choice_table.objects.create(
        id=choice_uuid,
        chainavailable=get_ms_chain_instance(
            apps,
            schema_editor,
            chain_uuid=chain_uuid
        ),
        choiceavailableatlink=get_ms_chain_link_instance(
            apps,
            schema_editor,
            ms_uuid=link_uuid
        ),
    )


def create_ms_dict_choice(
        apps, schema_editor,
        choice_uuid, desc, replacement_dict, link_uuid):
    """Create a dictionary based choice in the database."""
    microservice_dict_choice_table = apps\
        .get_model('main', 'MicroServiceChoiceReplacementDic')
    microservice_dict_choice_table.objects.create(
        id=choice_uuid,
        description=desc,
        choiceavailableatlink=get_ms_chain_link_instance(
            apps,
            schema_editor,
            ms_uuid=link_uuid
        ),
        replacementdic=replacement_dict,
    )


def create_ms_exit_codes(
        apps, schema_editor,
        exit_code_uuid, ms_in, ms_out,
        ms_exit_code=MS_EXIT_CODE, ms_exit_message=MS_COMPLETED_SUCCESSFULLY):
    """Create an exit code entry in the database."""
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    MicroServiceChainLinkExitCode.objects.create(
        id=exit_code_uuid,
        microservicechainlink_id=ms_in,
        exitcode=ms_exit_code,
        nextmicroservicechainlink_id=ms_out,
        exitmessage=ms_exit_message,
    )
    return


# Functions to help return ORM object instances for various MS entries.
def get_ms_chain_instance(apps, schema_editor, chain_uuid):
    """Return an object instance of a Microservice Chain to the calling
    function.
    """
    return apps\
        .get_model("main", "MicroServiceChain")\
        .objects.get(id=chain_uuid)


def get_ms_chain_link_instance(apps, schema_editor, ms_uuid):
    """Get chainlink instance from the database."""
    return apps\
        .get_model("main", "MicroServiceChainLink")\
        .objects.get(id=ms_uuid)


def get_task_type_instance(apps, schema_editor, task_type_uuid):
    """Get a task type instance from the database."""
    return apps\
        .get_model('main', 'TaskType')\
        .objects.get(id=task_type_uuid)


def get_watched_type_instance(apps, schema_editor, type_uuid):
    """Return a watched directory type from the database."""
    return apps\
        .get_model('main', 'WatchedDirectoryExpectedType')\
        .objects.get(id=type_uuid)


# Primary entry point for the data migration.
def read_workflow(apps, schema_editor, workflow):
    """Read a workflow file into the database."""
    json_data = read_json(workflow)
    read_json_links(apps, schema_editor, json_data)
