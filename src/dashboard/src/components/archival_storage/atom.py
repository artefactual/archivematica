# -*- coding: utf-8 -*-
# This file is part of Archivematica.
#
# Copyright 2010-2016 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import

import logging
import os
import tempfile

import requests

from agentarchives.atom.client import AtomClient, AtomError, CommunicationError
from metsrw import METSDocument
from storageService import extract_file

from main.models import DashboardSetting

logger = logging.getLogger("archivematica.dashboard")


def get_atom_client():
    settings = DashboardSetting.objects.get_dict("upload-qubit_v0.0")
    return AtomClient(settings.get("url"), settings.get("key"))


class AtomMetadataUploadError(Exception):
    pass


def _load_premis(data, mwfile):
    """Update ``data`` dictionary with relevant ``PREMIS:OBJECT`` attrs."""
    try:
        premis_object = mwfile.get_premis_objects()[0]
    except IndexError:
        return
    props = (
        "size",
        "format_name",
        "format_version",
        "format_registry_name",
        "format_registry_key",
    )
    for prop in props:
        try:
            val = getattr(premis_object, prop)
        except AttributeError:
            continue
        # Calling `getattr` to find an attribute deeper in the `premis_object`
        # structure returns a non JSON serializable tuple instead of a None
        # value. See Issues#743 for more information.
        if not val or isinstance(val, tuple):
            continue
        logger.debug("Extracted property %s from METS: %s", prop, val)
        data[prop] = val


def upload_dip_metadata_to_atom(aip_name, aip_uuid, parent_slug):
    """
    Write to a AtoM's resource (parent_slug) the metadata of the objects of a
    AIP given its name and UUID. Return the slug of the new container resource
    created to hold the metadata objects.
    """
    with tempfile.NamedTemporaryFile() as temp:
        # Download METS file
        mets_path = "{}-{}/data/METS.{}.xml".format(aip_name, aip_uuid, aip_uuid)
        logger.debug("Extracting file %s into %s", mets_path, temp.name)
        try:
            extract_file(aip_uuid, mets_path, temp.name)
        except requests.exceptions.RequestException:
            raise AtomMetadataUploadError

        client = get_atom_client()
        mw = METSDocument.fromfile(temp.name)

        # Create file container
        try:
            logger.info(
                "Creating file container with slug %s and title %s",
                parent_slug,
                aip_name,
            )
            file_slug = client.add_child(
                parent_slug=parent_slug, title=aip_name, level="File"
            )
        except (AtomError, CommunicationError):
            raise AtomMetadataUploadError

        # Add objects
        for item in mw.all_files():
            if item.type == "Directory" or item.use != "original":
                continue
            attrs = {
                "title": os.path.basename(item.path),
                "usage": "Offline",
                "file_uuid": item.file_uuid,
                "aip_uuid": aip_uuid,
                "aip_name": aip_name,
                "relative_path_within_aip": item.path,
            }
            _load_premis(attrs, item)
            title = os.path.basename(item.path)
            try:
                logger.info("Creating child with title %s", title)
                slug = client.add_child(
                    parent_slug=file_slug, title=title, level="Item"
                )
                logger.info("Adding digital object to new child with slug %s", slug)
                client.add_digital_object(slug, **attrs)
            except (AtomError, CommunicationError):
                raise AtomMetadataUploadError

        return file_slug
