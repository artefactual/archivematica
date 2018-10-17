# -*- coding: utf-8 -*-

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
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

"""Where third party PID values are provided to Archivematica in the
``identifiers.json`` file update the ``Identifiers`` model to also include the
values supplied in that file.
"""
import json
from os import path

from bind_pid_helpers import BindPIDsException, \
    _add_custom_pid_to_mdl_identifiers
from main.models import Directory, File, SIP

from django.core.exceptions import ObjectDoesNotExist


IDENTIFIERS_JSON = "identifiers.json"
SIPDIR = "%SIPDirectory%"

ISSIP = "sip"
ISDIR = "directory"
ISFILE = "file"


def create_absolute_objects_path(filepath, sip_loc):
    return path.join(sip_loc, filepath)


def create_sip_objects_path(filepath, sip_loc):
    return "{}{}".format(SIPDIR, filepath)


def context(filepath):
    if filepath.endswith("objects") or filepath.endswith('objects/'):
        return ISSIP
    if path.isdir(filepath):
        return ISDIR
    if path.isfile(filepath):
        return ISFILE


def parse_identifiers_json(job, logger, json_data, sip_loc, sip_uuid):
    for path_ in json_data:
        try:
            object_path = path_['file']
        except KeyError:
            # Assume that other files in ``identifiers.json`` may still match.
            continue
        # Don't assume that there is an objects folder in the metadata supplied
        # by the user.
        logger.info("1. VAR %s", object_path)
        obj_check = path.split(object_path)[0]
        if obj_check != "objects":
            logger.info("2. VAR adding objects %s", object_path)
            object_path = path.join("objects", object_path)
        logger.info("3. VAR %s", object_path)
        abs_object_path = create_absolute_objects_path(object_path, sip_loc)
        sip_object_path = create_sip_objects_path(object_path, sip_loc)
        logger.error("Looking for object: %s", sip_object_path)
        try:
            unit_type = context(abs_object_path)
            if unit_type is ISSIP:
                mdl = SIP.objects.get(uuid=sip_uuid)
            elif unit_type is ISDIR:
                mdl = Directory.objects.get(
                    sip_id=sip_uuid,
                    currentlocation=path.join(sip_object_path, ''))
            elif unit_type is ISFILE:
                mdl = File.objects.get(
                    sip_id=sip_uuid, currentlocation=sip_object_path)
        except ObjectDoesNotExist:
            logger.warning(
                "Cannot find unit type: %s in the db, path: %s",
                unit_type, sip_object_path)
            continue
        job.pyprint("Found {}".format(mdl))
        try:
            pids = path_["identifiers"]
        except KeyError:
            logger.warning("Cannot find identifiers for: %s", sip_object_path)
            continue
        for ids in pids:
            try:
                identifier = ids["identifier"]
                scheme = ids["identiferType"]
            except KeyError:
                logger.warning(
                    "Cannot find identifier for unit type %s, path: %s",
                    unit_type, sip_object_path)
                continue
            job.pyprint(
                "Discovered identifier type: {} value: {} for: {}"
                .format(scheme, identifier, sip_object_path))
            _add_custom_pid_to_mdl_identifiers(mdl, scheme, identifier)


def load_identifiers_json(job, logger, sip_uuid, identifiers_loc, shared_path):
    try:
        sip_loc = SIP.objects.get(uuid=sip_uuid).currentpath\
            .replace("%sharedPath%", shared_path)
    except SIP.DoesNotExist:
        raise BindPIDsException("Cannot find SIP %s", sip_uuid)
    identifiers_loc = \
        identifiers_loc.currentlocation.replace(
            SIPDIR, sip_loc)
    if path.exists(identifiers_loc):
        job.pyprint("Loading PIDs from identifiers.json")
        with open(identifiers_loc) as json_data_file:
            try:
                json_data = json.load(json_data_file)
            except ValueError as err:
                raise BindPIDsException("JSON decode error: %s", err)
            parse_identifiers_json(job, logger, json_data, sip_loc, sip_uuid)
