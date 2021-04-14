# -*- coding: utf-8 -*-

"""Processing configuration.

This module lists the processing configuration fields where the user has the
ability to establish predefined choices via the user interface, and handles
processing config file operations.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import abc
import logging
import os
import shutil

from django.conf import settings
from lxml import etree
import six

from server.workflow_abilities import choice_is_available
import storageService as storage_service


logger = logging.getLogger("archivematica.mcp.server.processing_config")


@six.add_metaclass(abc.ABCMeta)
class ProcessingConfigField(object):
    def __init__(self, link_id, name, **kwargs):
        self.link_id = link_id
        self.name = name
        self.options = self.read_config(kwargs)

    @abc.abstractmethod
    def read_config(self, options):
        """Implementors must use this method to process additional config."""

    @abc.abstractmethod
    def add_choices(self, workflow, lang):
        """Implementors must use this method to add field choices."""

    def to_dict(self, workflow, lang):
        """It generates a dictionary with all the information needed to feed
        a drop-down, including its choices and where they apply in workflow
        which can be more than a single entry.

        E.g., "Normalize for preservation" is a chain link shared across more
        than a single decision point.
        """
        self.link = workflow.get_link(self.link_id)
        self.choices = []
        self.add_choices(workflow, lang)
        return {
            "id": self.link.id,
            "name": self.name,
            "label": self.link.get_label("description", lang),
            "choices": self.choices,
        }


class StorageLocationField(ProcessingConfigField):
    ALLOWED_PURPOSES = ("AS", "DS")

    def read_config(self, options):
        self.purpose = options["purpose"]
        if self.purpose not in self.ALLOWED_PURPOSES:
            raise ValueError(
                "Purpose %s is invalid; valid purposes: %s."
                % (self.purpose, ", ".join(self.ALLOWED_PURPOSES))
            )

    def add_choices(self, workflow, lang):
        value = "/api/v2/location/default/%s/" % self.purpose
        self.choices.append(
            {
                "value": value,
                "label": "Default location",
                "applies_to": [(self.link.id, value, "Default location")],
            }
        )

        locations = self.get_storage_locations()
        if locations:
            for loc in locations:
                label = loc["description"] or loc["relative_path"]
                self.choices.append(
                    {
                        "value": loc["resource_uri"],
                        "label": label,
                        "applies_to": [(self.link.id, loc["resource_uri"], label)],
                    }
                )

    def get_storage_locations(self):
        return storage_service.get_location(purpose=self.purpose)


class ReplaceDictField(ProcessingConfigField):
    def read_config(self, options):
        pass

    def add_choices(self, workflow, lang):
        for item in self.link.config["replacements"]:
            label = item["description"].get_label(lang)
            self.choices.append(
                {
                    "value": item["id"],
                    "label": label,
                    "applies_to": [(self.link.id, item["id"], label)],
                }
            )


class ChainChoicesField(ProcessingConfigField):
    """Populate choices based on the list of chains indicated by
    ``chain_choices`` in the workflow link definition.

    ``ignored_choices`` (List[str]) is an optional list of chain names that will
    not be incorporated. ``find_duplicates`` is an optional string used to match
    all links making use of that choice, e.g. "Normalize for preservation".
    """

    def read_config(self, options):
        self.ignored_choices = options.get("ignored_choices", [])
        self.find_duplicates = options.get("find_duplicates")

    def add_choices(self, workflow, lang):
        for chain_id in self.link.config["chain_choices"]:
            chain = workflow.get_chain(chain_id)
            chain_desc = chain.get_label("description")
            if chain_desc in self.ignored_choices:
                continue
            if not choice_is_available(self.link, chain):
                continue
            self.choices.append(
                {
                    "value": chain_id,
                    "label": chain.get_label("description", lang),
                    "applies_to": [(self.link_id, chain_id, chain_desc)],
                }
            )
            if not self.find_duplicates:
                continue
            for link in workflow.get_links().values():
                if link.id == self.link_id:
                    continue
                if link.get_label("description") != self.find_duplicates:
                    continue
                for cid in link.config["chain_choices"]:
                    chain = workflow.get_chain(cid)
                    if chain_desc != chain.get_label("description"):
                        continue
                    self.choices[-1]["applies_to"].append(
                        (link.id, chain.id, chain_desc)
                    )


class SharedChainChoicesField(ProcessingConfigField):
    """Populate choices that are equivalent across multiple chain links.

    Use `related_links` (List[str]) to indicate additional link identifiers.
    """

    def read_config(self, options):
        self.related_links = options.get("related_links", [])

    def add_choices(self, workflow, lang):
        # Full list of choices based on the master link.
        choices = [
            workflow.get_chain(chain_id)["description"]["en"]
            for chain_id in self.link.config["chain_choices"]
        ]

        # All link identifiers.
        link_ids = [self.link.id] + self.related_links

        # Each choice capturing the underlying chain choices for each link,
        for choice in choices:
            applies_to = []
            value = None
            for link_id in link_ids:
                link = workflow.get_link(link_id)
                for chain_id in link.config["chain_choices"]:
                    chain = workflow.get_chain(chain_id)
                    if chain.get_label("description") == choice:
                        applies_to.append((link_id, chain_id, choice))
                        if link_id == self.link.id:
                            value = chain_id
            self.choices.append(
                {"value": value, "label": choice, "applies_to": applies_to}
            )


# A list of processing configuration fields that we want to display via the
# web user interface. Use one of the supported configuration classes, i.e. all
# classes extending ``ProcessingConfigField``.
processing_fields = [
    SharedChainChoicesField(
        link_id="856d2d65-cd25-49fa-8da9-cabb78292894",
        name="virus_scanning",
        related_links=[
            "1dad74a2-95df-4825-bbba-dca8b91d2371",
            "7e81f94e-6441-4430-a12d-76df09181b66",
            "390d6507-5029-4dae-bcd4-ce7178c9b560",
            "97a5ddc0-d4e0-43ac-a571-9722405a0a9b",
        ],
    ),
    ReplaceDictField(
        link_id="bd899573-694e-4d33-8c9b-df0af802437d",
        name="assign_uuids_to_directories",
    ),
    ChainChoicesField(
        link_id="56eebd45-5600-4768-a8c2-ec0114555a3d",
        name="generate_transfer_structure",
    ),
    ReplaceDictField(
        link_id="f09847c2-ee51-429a-9478-a860477f6b8d",
        name="select_format_id_tool_transfer",
    ),
    ChainChoicesField(
        link_id="dec97e3c-5598-4b99-b26e-f87a435a6b7f", name="extract_packages"
    ),
    ReplaceDictField(
        link_id="f19926dd-8fb5-4c79-8ade-c83f61f55b40", name="delete_packages"
    ),
    ChainChoicesField(
        link_id="70fc7040-d4fb-4d19-a0e6-792387ca1006", name="policy_checks_originals"
    ),
    ChainChoicesField(
        link_id="accea2bf-ba74-4a3a-bb97-614775c74459", name="examine_contents"
    ),
    ChainChoicesField(
        link_id="bb194013-597c-4e4a-8493-b36d190f8717",
        name="create_sip",
        ignored_choices=["Reject transfer"],
    ),
    ReplaceDictField(
        link_id="7a024896-c4f7-4808-a240-44c87c762bc5",
        name="select_format_id_tool_ingest",
    ),
    ChainChoicesField(
        link_id="cb8e5706-e73f-472f-ad9b-d1236af8095f",
        name="normalize",
        ignored_choices=["Reject SIP"],
        find_duplicates="Normalize",
    ),
    ChainChoicesField(
        link_id="de909a42-c5b5-46e1-9985-c031b50e9d30",
        name="normalize_transfer",
        ignored_choices=["Redo", "Reject"],
    ),
    ReplaceDictField(
        link_id="498f7a6d-1b8c-431a-aa5d-83f14f3c5e65", name="normalize_thumbnail_mode"
    ),
    ChainChoicesField(
        link_id="153c5f41-3cfb-47ba-9150-2dd44ebc27df",
        name="policy_checks_preservation_derivatives",
    ),
    ChainChoicesField(
        link_id="8ce07e94-6130-4987-96f0-2399ad45c5c2",
        name="policy_checks_access_derivatives",
    ),
    ChainChoicesField(link_id="a2ba5278-459a-4638-92d9-38eb1588717d", name="bind_pids"),
    ChainChoicesField(
        link_id="d0dfa5fc-e3c2-4638-9eda-f96eea1070e0", name="normative_structmap"
    ),
    ChainChoicesField(link_id="eeb23509-57e2-4529-8857-9d62525db048", name="reminder"),
    ChainChoicesField(
        link_id="82ee9ad2-2c74-4c7c-853e-e4eaf68fc8b6", name="transcribe_file"
    ),
    ReplaceDictField(
        link_id="087d27be-c719-47d8-9bbb-9a7d8b609c44",
        name="select_format_id_tool_submissiondocs",
    ),
    ReplaceDictField(
        link_id="01d64f58-8295-4b7b-9cab-8f1b153a504f", name="compression_algo"
    ),
    ReplaceDictField(
        link_id="01c651cb-c174-4ba4-b985-1d87a44d6754", name="compression_level"
    ),
    ChainChoicesField(
        link_id="2d32235c-02d4-4686-88a6-96f4d6c7b1c3",
        name="store_aip",
        ignored_choices=["Reject AIP"],
    ),
    StorageLocationField(
        link_id="b320ce81-9982-408a-9502-097d0daa48fa",
        name="store_aip_location",
        purpose="AS",
    ),
    ChainChoicesField(
        link_id="92879a29-45bf-4f0b-ac43-e64474f0f2f9", name="upload_dip"
    ),
    ChainChoicesField(link_id="5e58066d-e113-4383-b20b-f301ed4d751c", name="store_dip"),
    StorageLocationField(
        link_id="cd844b6e-ab3c-4bc6-b34f-7103f88715de",
        name="store_dip_location",
        purpose="DS",
    ),
]


def get_processing_fields(workflow, lang="en"):
    """Return the list dict form of all processing configuration fields defined
    in the module-level attribute ``processing_fields``.
    """
    return [field.to_dict(workflow, lang) for field in processing_fields]


def copy_processing_config(processing_config, destination_path):
    if processing_config is None:
        return

    src = os.path.join(
        settings.SHARED_DIRECTORY,
        "sharedMicroServiceTasksConfigs/processingMCPConfigs",
        "%sProcessingMCP.xml" % processing_config,
    )
    dest = os.path.join(destination_path, "processingMCP.xml")
    try:
        shutil.copyfile(src, dest)
    except IOError:
        logger.warning(
            "Processing configuration could not be copied: (from=%s to=%s)",
            src,
            dest,
            exc_info=True,
        )


def load_processing_xml(package_path):
    processing_file_path = os.path.join(package_path, settings.PROCESSING_XML_FILE)

    if not os.path.isfile(processing_file_path):
        return None

    try:
        return etree.parse(processing_file_path)
    except etree.LxmlError:
        logger.warning(
            "Error parsing xml at %s for pre-configured choice",
            processing_file_path,
            exc_info=True,
        )
        return None


def load_preconfigured_choice(package_path, workflow_link_id):
    choice = None

    processing_xml = load_processing_xml(package_path)
    if processing_xml is not None:
        for preconfigured_choice in processing_xml.findall(".//preconfiguredChoice"):
            if preconfigured_choice.find("appliesTo").text == str(workflow_link_id):
                choice = preconfigured_choice.find("goToChain").text

    return choice


def processing_configuration_file_exists(processing_configuration_name):
    if not processing_configuration_name:
        return False
    result = os.path.isfile(
        os.path.join(
            settings.SHARED_DIRECTORY,
            "sharedMicroServiceTasksConfigs/processingMCPConfigs",
            "%sProcessingMCP.xml" % processing_configuration_name,
        )
    )
    if not result:
        logger.debug(
            "Processing configuration file for %s does not exist",
            processing_configuration_name,
        )
    return result
