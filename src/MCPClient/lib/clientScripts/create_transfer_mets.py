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

import logging
import os
from optparse import OptionParser

import django
from django.db.models import Prefetch

django.setup()
import metsrw

# archivematicaCommon
from archivematicaFunctions import escape

# dashboard
from main.models import Derivation, File


PREMIS_VERSION = metsrw.plugins.premisrw.PREMIS_2_2_META
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
    db_base_path = r"%{}%".format(base_path_placeholder)
    lookup_kwargs = {identifier_group: identifier_uuid}

    mets = metsrw.METSDocument()
    root_fsentry = build_fsentries_tree(
        transfer_dir_path, transfer_dir_path, db_base_path, lookup_kwargs
    )
    mets.append_file(root_fsentry)

    mets.write(mets_path)


def build_fsentries_tree(path, root_path, db_base_path, lookup_kwargs, parent=None):
    """
    Recursively builds a tree of metsrw.FSEntry objects from the path given.

    Returns:
        The root metsrw.FSEntry
    """
    if parent is None:
        parent_path = os.path.basename(path)
        parent = metsrw.FSEntry(path=parent_path, type="Directory")

    for item_name in sorted(os.listdir(path)):
        item_full_path = os.path.join(path, item_name)
        is_directory = os.path.isdir(item_full_path)

        if is_directory:
            fsentry = metsrw.FSEntry(path=item_name, type="Directory")
        else:
            item_relative_path = os.path.relpath(item_full_path, start=root_path)
            file_obj = lookup_file_data(item_relative_path, db_base_path, lookup_kwargs)
            if file_obj is None:
                continue
            fsentry = metsrw.FSEntry(
                path=item_name,
                type="Item",
                file_uuid=file_obj.uuid,
                checksum=file_obj.checksum,
                checksumtype=file_obj.checksumtype,
            )

            premis_object = file_obj_to_premis(file_obj)
            fsentry.add_premis_object(premis_object)
            for event in file_obj.event_set.all():
                premis_event = event_to_premis(event)
                fsentry.add_premis_event(premis_event)

        parent.add_child(fsentry)

        if is_directory:
            build_fsentries_tree(
                item_full_path, root_path, db_base_path, lookup_kwargs, parent=fsentry
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


def file_obj_to_premis(file_obj):
    """
    Converts an File model object to a PREMIS event object via metsrw.

    Returns:
        metsrw.plugins.premisrw.premis.PREMISObject
    """

    premis_data = (
        "object",
        metsrw.plugins.premisrw.PREMIS_2_2_META,
        (
            "object_identifier",
            ("object_identifier_type", "UUID"),
            ("object_identifier_value", file_obj.uuid),
        ),
        (
            "object_characteristics",
            ("composition_level", "0"),
            (
                "fixity",
                ("message_digest_algorithm", file_obj.checksumtype.upper()),
                ("message_digest", file_obj.checksum),
            ),
            ("size", str(file_obj.size)),
            get_premis_format_data(file_obj.fileid_set.all()),
            (
                "creating_application",
                (
                    "date_created_by_application",
                    file_obj.modificationtime.strftime("%Y-%m-%d"),
                ),
            ),
        ),
        ("original_name", escape(file_obj.originallocation)),
    ) + get_premis_relationship_data(
        file_obj.related_is_source_of, file_obj.related_has_source
    )

    return metsrw.plugins.premisrw.data_to_premis(premis_data)


def event_to_premis(event):
    """
    Converts an Event model to a PREMIS event object via metsrw.

    Returns:
        metsrw.plugins.premisrw.premis.PREMISEvent
    """
    premis_data = (
        "event",
        metsrw.plugins.premisrw.PREMIS_2_2_META,
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

    return metsrw.plugins.premisrw.data_to_premis(premis_data)


def call(jobs):
    parser = OptionParser()
    parser.add_option("-s", "--basePath", action="store", dest="basePath", default="")
    parser.add_option(
        "-b",
        "--basePathString",
        action="store",
        dest="basePathString",
        default="SIPDirectory",
    )  # transferDirectory
    parser.add_option(
        "-f",
        "--fileGroupIdentifier",
        action="store",
        dest="fileGroupIdentifier",
        default="sipUUID",
    )  # transferUUID
    parser.add_option("-S", "--sipUUID", action="store", dest="sipUUID", default="")
    parser.add_option("-x", "--xmlFile", action="store", dest="xmlFile", default="")

    for job in jobs:
        with job.JobContext(logger=logger):
            (opts, args) = parser.parse_args(job.args[1:])
            write_mets(
                opts.xmlFile,
                opts.basePath,
                opts.basePathString,
                opts.fileGroupIdentifier,
                opts.sipUUID,
            )
