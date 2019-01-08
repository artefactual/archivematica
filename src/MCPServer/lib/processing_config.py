"""Processing configuration.

This module lists the processing configuration fields where the user has the
ability to establish predefined choices via the user interface.
"""

from collections import OrderedDict

from django.conf import settings as django_settings

from workflow_abilities import choice_is_available


# Types of processing fields:
# - "boolean" (required: "yes_option", "no_option")
# - "storage_service" (required: "purpose")
# - "days" (required: "chain")
# - "replace_dict"
# - "chain_choice" (optional: "ignored_choices", "find_duplicates")
processing_fields = OrderedDict()
processing_fields['bd899573-694e-4d33-8c9b-df0af802437d'] = {
    'type': 'boolean',
    'name': 'assign_uuids_to_directories',
    'yes_option': '2dc3f487-e4b0-4e07-a4b3-6216ed24ca14',
    'no_option': '891f60d0-1ba8-48d3-b39e-dd0934635d29',
}
processing_fields['755b4177-c587-41a7-8c52-015277568302'] = {
    'type': 'boolean',
    'name': 'quarantine_transfer',
    'yes_option': '97ea7702-e4d5-48bc-b4b5-d15d897806ab',
    'no_option': 'd4404ab1-dc7f-4e9e-b1f8-aa861e766b8e',
}
processing_fields['19adb668-b19a-4fcb-8938-f49d7485eaf3'] = {
    'type': 'days',
    'name': 'quarantine_expiry_days',
    'chain': '333643b7-122a-4019-8bef-996443f3ecc5',
}
processing_fields['56eebd45-5600-4768-a8c2-ec0114555a3d'] = {
    'type': 'boolean',
    'name': 'tree',
    'yes_option': 'df54fec1-dae1-4ea6-8d17-a839ee7ac4a7',
    'no_option': 'e9eaef1e-c2e0-4e3b-b942-bfb537162795',
}
processing_fields['f09847c2-ee51-429a-9478-a860477f6b8d'] = {
    'type': 'replace_dict',
    'name': 'select_format_id_tool_transfer',
}
processing_fields['dec97e3c-5598-4b99-b26e-f87a435a6b7f'] = {
    'type': 'chain_choice',
    'name': 'extract_packages',
}
processing_fields['f19926dd-8fb5-4c79-8ade-c83f61f55b40'] = {
    'type': 'replace_dict',
    'name': 'delete_packages',
}
processing_fields['70fc7040-d4fb-4d19-a0e6-792387ca1006'] = {
    'type': 'boolean',
    'name': 'policy_checks_originals',
    'yes_option': 'c611a6ff-dfdb-46d1-b390-f366a6ea6f66',
    'no_option': '3e891cc4-39d2-4989-a001-5107a009a223',
}
processing_fields['accea2bf-ba74-4a3a-bb97-614775c74459'] = {
    'type': 'chain_choice',
    'name': 'examine',
}
processing_fields['bb194013-597c-4e4a-8493-b36d190f8717'] = {
    'type': 'chain_choice',
    'name': 'create_sip',
    'ignored_choices': ['Reject transfer'],
}
processing_fields['7a024896-c4f7-4808-a240-44c87c762bc5'] = {
    'type': 'replace_dict',
    'name': 'select_format_id_tool_ingest',
}
processing_fields['cb8e5706-e73f-472f-ad9b-d1236af8095f'] = {
    'type': 'chain_choice',
    'name': 'normalize',
    'ignored_choices': ['Reject SIP'],
    'find_duplicates': True,
    'label': 'Normalize',
}
processing_fields['de909a42-c5b5-46e1-9985-c031b50e9d30'] = {
    'type': 'boolean',
    'name': 'normalize_transfer',
    'yes_option': '1e0df175-d56d-450d-8bee-7df1dc7ae815',
}
processing_fields['498f7a6d-1b8c-431a-aa5d-83f14f3c5e65'] = {
    'type': 'replace_dict',
    'name': 'normalize_thumbnail_mode',
}
processing_fields['153c5f41-3cfb-47ba-9150-2dd44ebc27df'] = {
    'type': 'boolean',
    'name': 'policy_checks_preservation_derivatives',
    'yes_option': '3a55f688-eca3-4ebc-a012-4ce68290e7b0',
    'no_option': 'b7ce05f0-9d94-4b3e-86cc-d4b2c6dba546',
}
processing_fields['8ce07e94-6130-4987-96f0-2399ad45c5c2'] = {
    'type': 'boolean',
    'name': 'policy_checks_access_derivatives',
    'yes_option': 'd9760427-b488-4381-832a-de10106de6fe',
    'no_option': '76befd52-14c3-44f9-838f-15a4e01624b0',
}
processing_fields['05357876-a095-4c11-86b5-a7fff01af668'] = {
    'type': 'boolean',
    'name': 'bind_pids',
    'yes_option': '1e79e1b6-cf50-49ff-98a3-fa51d73553dc',
    'no_option': 'fcfea449-158c-452c-a8ad-4ae009c4eaba',
}
processing_fields['d0dfa5fc-e3c2-4638-9eda-f96eea1070e0'] = {
    'type': 'boolean',
    'name': 'normative_structmap',
    'yes_option': '29881c21-3548-454a-9637-ebc5fd46aee0',
    'no_option': '65273f18-5b4e-4944-af4f-09be175a88e8',
}
processing_fields['eeb23509-57e2-4529-8857-9d62525db048'] = {
    'type': 'chain_choice',
    'name': 'reminder',
}
processing_fields['7079be6d-3a25-41e6-a481-cee5f352fe6e'] = {
    'type': 'boolean',
    'name': 'transcribe_file',
    'yes_option': '5a9985d3-ce7e-4710-85c1-f74696770fa9',
    'no_option': '1170e555-cd4e-4b2f-a3d6-bfb09e8fcc53',
}
processing_fields['087d27be-c719-47d8-9bbb-9a7d8b609c44'] = {
    'type': 'replace_dict',
    'name': 'select_format_id_tool_submissiondocs',
}
processing_fields['01d64f58-8295-4b7b-9cab-8f1b153a504f'] = {
    'type': 'replace_dict',
    'name': 'compression_algo',
}
processing_fields['01c651cb-c174-4ba4-b985-1d87a44d6754'] = {
    'type': 'replace_dict',
    'name': 'compression_level',
}
processing_fields['2d32235c-02d4-4686-88a6-96f4d6c7b1c3'] = {
    'type': 'boolean',
    'name': 'store_aip',
    'yes_option': '9efab23c-31dc-4cbd-a39d-bb1665460cbe',
}
processing_fields['b320ce81-9982-408a-9502-097d0daa48fa'] = {
    'type': 'storage_service',
    'name': 'store_aip_location',
    'purpose': 'AS',
}
processing_fields['92879a29-45bf-4f0b-ac43-e64474f0f2f9'] = {
    'type': 'chain_choice',
    'name': 'upload_dip',
}
processing_fields['5e58066d-e113-4383-b20b-f301ed4d751c'] = {
    'type': 'chain_choice',
    'name': 'store_dip',
}
processing_fields['cd844b6e-ab3c-4bc6-b34f-7103f88715de'] = {
    'type': 'storage_service',
    'name': 'store_dip_location',
    'purpose': 'DS',
}


def get_processing_fields(workflow):
    """Return the list of known processing configuration fields.

    It uses `processing_fields`` defined in this module as a base and extended
    after some workflow lookups.
    """
    for link_id, config in processing_fields.items():
        link = workflow.get_link(link_id)
        if config['type'] == 'replace_dict':
            config['options'] = _get_options_for_replace_dict(link)
        elif config['type'] == 'chain_choice':
            config['options'] = _get_options_for_chain_choice(
                link, workflow, config.get('ignored_choices', []))
            _populate_duplicates_chain_choice(workflow, link, config)
    return processing_fields


def _get_options_for_replace_dict(link):
    return [
        (item["id"], item["description"]["en"],)
        for item in link.config["replacements"]
    ]


def _get_options_for_chain_choice(link, workflow, ignored_choices):
    ret = []
    for chain_id in link.config["chain_choices"]:
        chain = workflow.get_chain(chain_id)
        label = chain.get_label("description")
        if label in ignored_choices:
            continue
        if not choice_is_available(link, chain, django_settings):
            continue
        ret.append((chain_id, label))
    return ret


def _populate_duplicates_chain_choice(workflow, link, config):
    """Find and populate chain choice duplicates.

    When the user chooses a value like "Normalize for preservation" in the
    "Normalize" processing config, this function makes sure that all the
    matching chain links are listed so the user choise applies to all of them.

    Given the following config item (see `processing_fields` in this module):

        config[find_duplicates] = True
        config[label] = "Normalize"
        config[options] = [
            (2b93cecd4-71f2-4e28-bc39-d32fd62c5a94", "Normalize ...")
            (2612e3609-ce9a-4df6-a9a3-63d634d2d934", ...)
            (2c34bd22a-d077-4180-bf58-01db35bdb644", ...)
            (289cb80dd-0636-464f-930d-57b61e3928b2", ...)
            (2a6ed697e-6189-4b4e-9f80-29209abc7937", ...)
            (2e600b56d-1a43-4031-9d7c-f64f123e5662", ...)
            (2fb7a326e-1e50-4b48-91b9-4917ff8d0ae8", ...)
        ]

    This function populates a new property with a list of matching links, e.g.:

        config[duplicates] = {
            <chain_id> = (chain_desc, (<link_id>, <chain_id>), ...)
            ...
        }

    It's used in `administration/forms.py` so we can build configs like the
    following when the user picks "Normalize for preservation" which has more
    than one match:

        <!-- Normalize (match 1 for "Normalize for preservation") -->
        <preconfiguredChoice>
          <appliesTo>cb8e5706-e73f-472f-ad9b-d1236af8095f</appliesTo>
          <goToChain>612e3609-ce9a-4df6-a9a3-63d634d2d934</goToChain>
        </preconfiguredChoice>
        <!-- Normalize (match 2 for "Normalize for preservation") -->
        <preconfiguredChoice>
          <appliesTo>7509e7dc-1e1b-4dce-8d21-e130515fce73</appliesTo>
          <goToChain>612e3609-ce9a-4df6-a9a3-63d634d2d934</goToChain>
        </preconfiguredChoice>
    """
    if not config.get("find_duplicates", False):
        return
    config["duplicates"] = {}
    for chain_id, chain_desc in config["options"]:
        results = []
        for link in workflow.get_links().values():
            if config["label"] != link.get_label("description"):
                continue
            for chain_id in link.config["chain_choices"]:
                chain = workflow.get_chain(chain_id)
                if chain_desc != chain.get_label("description"):
                    continue
                results.append((link.id, chain.id))
        config["duplicates"][chain_id] = (chain_desc, results)
