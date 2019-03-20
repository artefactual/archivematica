#!/usr/bin/env python2
#
# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
from __future__ import unicode_literals

import argparse
import logging
import os

import django
import scandir
from lxml import etree
from django.db.models import Prefetch

django.setup()
import metsrw

# archivematicaCommon
from archivematicaFunctions import get_dashboard_uuid, escape

# dashboard
from main.models import Derivation, File, FPCommandOutput


PREMIS_META = metsrw.plugins.premisrw.PREMIS_3_0_META

logger = logging.getLogger(__name__)


def write_mets(
    mets_path,
    transfer_dir_path,
    base_path_placeholder,
    identifier_group,
    identifier_uuid,
):
    """
    Writes a METS XML file to disk, containing all the data we can find.

    Args:
        mets_path: Output path for METS XML output
        transfer_dir_path: Location of the files on disk
        base_path_placeholder: The placeholder string for the base path, e.g. 'transferDirectory'
        identifier_group: The database column used to lookup file UUIDs, e.g. 'transfer_id'
        identifier_uuid: The UUID for the identifier group lookup
    """
    transfer_dir_path = os.path.expanduser(transfer_dir_path)
    transfer_dir_path = os.path.normpath(transfer_dir_path)

    db_base_path = r"%{}%".format(base_path_placeholder)
    lookup_kwargs = {identifier_group: identifier_uuid}

    mets = metsrw.METSDocument()
    mets.objid = str(identifier_uuid)

    dashboard_uuid = get_dashboard_uuid()
    if dashboard_uuid:
        agent = metsrw.Agent(
            "CREATOR",
            type="SOFTWARE",
            name=str(dashboard_uuid),
            notes=["Archivematica dashboard UUID"],
        )
        mets.agents.append(agent)

        # TODO: accession number

    root_fsentry = build_fsentries_tree(
        transfer_dir_path, transfer_dir_path, db_base_path, lookup_kwargs
    )
    mets.append_file(root_fsentry)
    mets.write(mets_path, pretty_print=True)


def convert_to_premis_hash_function(hash_type):
    """
    Returns a PREMIS valid hash function name, if possible.
    """
    if hash_type.lower().startswith("sha") and "-" not in hash_type:
        hash_type = "SHA-" + hash_type.upper()[3:]
    elif hash_type.lower() == "md5":
        return "MD5"

    return hash_type


def build_fsentries_tree(path, root_path, db_base_path, lookup_kwargs, parent=None):
    """
    Recursively builds a tree of metsrw.FSEntry objects from the path given.

    Returns:
        The root metsrw.FSEntry
    """
    if parent is None:
        parent_path = os.path.basename(path)
        parent = metsrw.FSEntry(path=parent_path, type="Directory")

    dir_entries = sorted(scandir.scandir(path), key=lambda d: d.name)
    for dir_entry in dir_entries:
        relative_path = os.path.relpath(dir_entry.path, start=root_path)

        if dir_entry.is_dir():
            fsentry = metsrw.FSEntry(
                path=relative_path, label=dir_entry.name, type="Directory"
            )
        else:
            file_obj = lookup_file_data(relative_path, db_base_path, lookup_kwargs)
            if file_obj is None:
                continue
            checksum_type = convert_to_premis_hash_function(file_obj.checksumtype)
            fsentry = metsrw.FSEntry(
                path=relative_path,
                label=dir_entry.name,
                type="Item",
                file_uuid=file_obj.uuid,
                checksum=file_obj.checksum,
                checksumtype=checksum_type,
            )

            premis_object = file_obj_to_premis(file_obj)
            fsentry.add_premis_object(premis_object)
            for event in file_obj.event_set.all():
                premis_event = event_to_premis(event)
                fsentry.add_premis_event(premis_event)

        parent.add_child(fsentry)

        if dir_entry.is_dir():
            build_fsentries_tree(
                dir_entry.path, root_path, db_base_path, lookup_kwargs, parent=fsentry
            )

    return parent


def lookup_file_data(relative_path, db_base_path, lookup_kwargs):
    """
    Given a file path, lookup everything we can from the database and cache it on the
    File object.

    Reads from File, FileFormatVersion, FormatVersion, Format and FPCommandOutput.
    """
    db_file_path = "".join([db_base_path, relative_path])
    db_lookup = {"removedtime__isnull": True}
    db_lookup.update(**lookup_kwargs)
    db_lookup["currentlocation"] = db_file_path

    # We need to do a lot of lookups here, so batch as much as possible.
    derivations_with_events = Derivation.objects.filter(event__isnull=False)
    characterization_commands = FPCommandOutput.objects.filter(
        rule__purpose__in=["characterization", "default_characterization"]
    )
    prefetches = [
        "event_set",
        "event_set__agents",
        "fileid_set",
        Prefetch(
            "original_file_set",
            queryset=derivations_with_events,
            to_attr="related_has_source",
        ),
        Prefetch(
            "derived_file_set",
            queryset=derivations_with_events,
            to_attr="related_is_source_of",
        ),
        Prefetch(
            "fpcommandoutput_set",
            queryset=characterization_commands,
            to_attr="characterization_documents",
        ),
    ]
    try:
        file_obj = File.objects.prefetch_related(*prefetches).get(**db_lookup)
    except File.DoesNotExist:
        logger.info("No record in database for file: %s", db_file_path)
        return None

    return file_obj


def get_premis_format_data(file_ids):
    format_data = ()

    for file_id in file_ids:
        format_data += (
            "format",
            (
                "format_designation",
                ("format_name", file_id.format_name),
                ("format_version", file_id.format_version),
            ),
            (
                "format_registry",
                ("format_registry_name", file_id.format_registry_name),
                ("format_registry_key", file_id.format_registry_key),
            ),
        )
    if not format_data:
        # default to unknown
        format_data = ("format", ("format_designation", ("format_name", "Unknown")))

    return format_data


def get_premis_relationship_data(derivations, originals):
    relationship_data = ()

    for derivation in derivations:
        relationship_data += (
            (
                "relationship",
                ("relationship_type", "derivation"),
                ("relationship_sub_type", "is source of"),
                (
                    "related_object_identification",
                    ("related_object_identifier_type", "UUID"),
                    ("related_object_identifier_value", derivation.derived_file_id),
                ),
                (
                    "related_event_identification",
                    ("related_event_identifier_type", "UUID"),
                    ("related_event_identifier_value", derivation.event_id),
                ),
            ),
        )
    for original in originals:
        relationship_data += (
            (
                "relationship",
                ("relationship_type", "derivation"),
                ("relationship_sub_type", "has source"),
                (
                    "related_object_identification",
                    ("related_object_identifier_type", "UUID"),
                    ("related_object_identifier_value", original.source_file_id),
                ),
                (
                    "related_event_identification",
                    ("related_event_identifier_type", "UUID"),
                    ("related_event_identifier_value", original.event_id),
                ),
            ),
        )

    return relationship_data


def get_premis_object_characteristics_extension(documents):
    extensions = ()

    for document in documents:
        # lxml will complain if we pass unicode, even if the XML
        # is UTF-8 encoded.
        # See https://lxml.de/parsing.html#python-unicode-strings
        # This only covers the UTF-8 and ASCII cases.
        xml_element = etree.fromstring(document.content.encode("utf-8"))

        extensions += ("object_characteristics_extension", xml_element)

    return extensions


def file_obj_to_premis(file_obj):
    """
    Converts an File model object to a PREMIS event object via metsrw.

    Returns:
        metsrw.plugins.premisrw.premis.PREMISObject
    """

    premis_digest_algorithm = convert_to_premis_hash_function(file_obj.checksumtype)
    format_data = get_premis_format_data(file_obj.fileid_set.all())
    original_name = escape(file_obj.originallocation)
    object_characteristics_extensions = get_premis_object_characteristics_extension(
        file_obj.characterization_documents
    )
    relationship_data = get_premis_relationship_data(
        file_obj.related_is_source_of, file_obj.related_has_source
    )

    object_characteristics = (
        "object_characteristics",
        ("composition_level", "0"),
        (
            "fixity",
            ("message_digest_algorithm", premis_digest_algorithm),
            ("message_digest", file_obj.checksum),
        ),
        ("size", str(file_obj.size)),
        format_data,
        (
            "creating_application",
            (
                "date_created_by_application",
                file_obj.modificationtime.strftime("%Y-%m-%d"),
            ),
        ),
    )
    if object_characteristics_extensions:
        object_characteristics += (object_characteristics_extensions,)

    premis_data = (
        "object",
        PREMIS_META,
        (
            "object_identifier",
            ("object_identifier_type", "UUID"),
            ("object_identifier_value", file_obj.uuid),
        ),
        object_characteristics,
        ("original_name", original_name),
    ) + relationship_data

    return metsrw.plugins.premisrw.data_to_premis(
        premis_data, premis_version=PREMIS_META["version"]
    )


def event_to_premis(event):
    """
    Converts an Event model to a PREMIS event object via metsrw.

    Returns:
        metsrw.plugins.premisrw.premis.PREMISEvent
    """
    premis_data = (
        "event",
        PREMIS_META,
        (
            "event_identifier",
            ("event_identifier_type", "UUID"),
            ("event_identifier_value", event.event_id),
        ),
        ("event_type", event.event_type),
        ("event_date_time", event.event_datetime),
        ("event_detail", event.event_detail),
        (
            "event_outcome_information",
            ("event_outcome", event.event_outcome),
            (
                "event_outcome_detail",
                ("event_outcome_detail_note", event.event_outcome_detail),
            ),
        ),
    )
    for agent in event.agents.all():
        premis_data += (
            (
                "linking_agent_identifier",
                ("linking_agent_identifier_type", agent.identifiertype),
                ("linking_agent_identifier_value", agent.identifiervalue),
            ),
        )

    return metsrw.plugins.premisrw.data_to_premis(
        premis_data, premis_version=PREMIS_META["version"]
    )


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--basePath", dest="base_path")
    parser.add_argument(
        "-b", "--basePathString", dest="base_path_string", default="SIPDirectory"
    )
    parser.add_argument(
        "-f", "--fileGroupIdentifier", dest="file_group_identifier", default="sipUUID"
    )
    parser.add_argument("-S", "--sipUUID", dest="sip_uuid")
    parser.add_argument("-x", "--xmlFile", dest="xml_file")

    for job in jobs:
        with job.JobContext(logger=logger):
            args = parser.parse_args(job.args[1:])
            write_mets(
                args.xml_file,
                args.base_path,
                args.base_path_string,
                args.file_group_identifier,
                args.sip_uuid,
            )
