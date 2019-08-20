#!/usr/bin/env python2
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

"""Bind a PID to the input ``SIP`` model and possibly also to all of the
``Directory`` models corresponding to all of the subdirectories within the SIP.

Binding a PID means making a single request to a Handle web API endpoint to:

1. request that the SIP's Transfer's accession number (or Directory's UUID) be
   registered as a handle (i.e., persistent identifier or PID), and
2. configure that PID/UUID-as-URL, i.e., PURL, to resolve to a base "resolve"
   URL and possibly also configure a number of qualified PURLs to resolve to
   related "resolve" URLs.

The idea is to allow for PURL resolution like:

    http://<PID-RESOLVER>/<NAME_AUTH>/<PID>
        => http://my-org-domain.org/dip/<PID>
    http://<PID-RESOLVER>/<NAME_AUTH>/<PID>?locatt=view:mets
        => http://my-org-domain.org/mets/<PID>

The required arguments are the SIP's UUID and the path to the
shared directory where SIPs are stored. If the --bind-pids option is something
other than 'Yes', the script will continue to the next job without doing anything.
"""

import argparse
from functools import wraps
from itertools import chain
import os
import sys

import django

django.setup()
from django.db import transaction
from lxml import etree

# dashboard
from main.models import DashboardSetting, Directory, SIP

# archivematicaCommon
from archivematicaFunctions import str2bool
from bindpid import (
    bind_pid,
    BindPIDException,
    _validate_handle_server_config,
    _validate_entity_type_required_params,
)
from custom_handlers import get_script_logger
import namespaces as ns


logger = get_script_logger("archivematica.mcp.client.bind_pids")


class BindPIDsException(Exception):
    """If I am raised, return 1."""

    exit_code = 1


def exit_on_known_exception(func):
    """Decorator that makes this module's ``main`` function cleaner by handling
    early exiting by catching particular exceptions.
    """

    @wraps(func)
    def wrapped(*_args, **kwargs):
        try:
            func(*_args, **kwargs)
        except BindPIDsException as exc:
            return exc.exit_code

    return wrapped


def _add_pid_to_mdl_identifiers(mdl, config):
    """Add the newly minted handle/PID to the ``SIP`` or ``Directory`` model as
    an identifier in its m2m ``identifiers`` attribute. Also add the PURL (URL
    constructed out of the PID) as a URI-type identifier.
    """
    pid = "{}/{}".format(config["naming_authority"], config["desired_pid"])
    purl = "{}/{}".format(config["handle_resolver_url"].rstrip("/"), pid)
    mdl.add_custom_identifier(scheme="hdl", value=pid)
    mdl.add_custom_identifier(scheme="URI", value=purl)


def _get_sip(sip_uuid):
    try:
        return SIP.objects.get(uuid=sip_uuid)
    except SIP.DoesNotExist:
        raise BindPIDsException


def _is_transfer_name(fname):
    """Return ``True`` only if ``fname`` is a possible transfer name, e.g.,
    something like ``'transfer-dingo-d90d427a-4475-4f2f-b117-0d8835ed1ac3'``."""
    return fname.startswith("transfer-") and [
        len(x) for x in fname.split("-")[-5:]
    ] == [8, 4, 4, 4, 12]


def _get_unique_transfer_mets_path(current_path):
    """Return the path to the METS file of the unique transfer contained within
    this SIP's directory; return ``None`` if there is no unique transfer.
    """
    transfers_path = os.path.join(current_path, "objects", "submissionDocumentation")
    transfer_paths = [
        os.path.join(transfers_path, fname)
        for fname in os.listdir(transfers_path)
        if _is_transfer_name(fname)
    ]
    if len(transfer_paths) == 1:
        transfer_mets_path = os.path.join(transfer_paths[0], "METS.xml")
        if os.path.isfile(transfer_mets_path):
            return transfer_mets_path
    return None


def _get_accession_no(transfer_mets_path):
    """Return the accession number by parsing a transfer METS file, or ``None``
    if there is no applicable element.
    """
    mets_doc = etree.parse(transfer_mets_path)
    return mets_doc.findtext("mets:metsHdr/mets:altRecordID", namespaces=ns.NSMAP)


def _get_unique_acc_no(sip_mdl, shared_path):
    """Return the accession number assigned to the unique transfer within the
    SIP represented by model ``sip_mdl``; if there is not such a unique
    transfer, or if it does not have an accession number, return ``None``.
    """
    current_path = sip_mdl.currentpath.replace("%sharedPath%", shared_path)
    unique_transfer_mets_path = _get_unique_transfer_mets_path(current_path)
    if unique_transfer_mets_path:
        accession_no = _get_accession_no(unique_transfer_mets_path)
        if accession_no:
            return accession_no
    return None


def _get_desired_pid(job, mdl, is_sip, shared_path, pid_source):
    """The desired PID is always the UUID for a directory. If the user has
    configured the accession number to be used for an AIP's PID, then we will
    try to use that here, if there is a unique one.
    """
    if is_sip and pid_source == "accession_no":
        unique_acc_no = _get_unique_acc_no(mdl, shared_path)
        if unique_acc_no:
            return unique_acc_no
        msg = (
            "Unable to find a unique accession number for SIP %s. Using its"
            " UUID as the PID instead",
            mdl.uuid,
        )
        logger.warning(msg)
        job.pyprint(msg)
    return mdl.uuid


def _bind_pid_to_model(job, mdl, shared_path, config):
    """Binds a PID (Handle persistent identifier) to the (SIP or Directory)
    model ``mdl`` by making a request to a Handle web service endpoint, given
    the configuration in ``config`` (which is configured in a dashboard form).
    Uses ``bind_pid`` from the bindpid.py module in archivematicaCommon. If
    successful, adds the PID to the model's ``identifiers`` attribute.
    """
    is_sip = isinstance(mdl, SIP)
    entity_type = (
        "unit" if is_sip else "file"
    )  # bindpid treats directories and files equivalently
    # Desired PID is usually model's UUID, but can be accession number
    desired_pid = _get_desired_pid(
        job, mdl, is_sip, shared_path, config["handle_archive_pid_source"]
    )
    config.update({"entity_type": entity_type, "desired_pid": desired_pid})
    _validate_entity_type_required_params(config)
    try:
        msg = bind_pid(**config)
        _add_pid_to_mdl_identifiers(mdl, config)
        job.pyprint(msg)  # gets appended to handles.log file, cf. StandardTaskConfig
        logger.info(msg)
        return 0
    except BindPIDException as exc:
        job.pyprint(exc, file=sys.stderr)
        logger.info(exc)
        raise BindPIDsException


@exit_on_known_exception
def main(job, sip_uuid, shared_path):
    """Bind the UUID ``sip_uuid`` to the appropriate URL(s), given the
    configuration in the dashboard, Do this only if ``bind_pids_switch`` is
    ``True``.
    """
    handle_config = DashboardSetting.objects.get_dict("handle")
    handle_config["pid_request_verify_certs"] = str2bool(
        handle_config.get("pid_request_verify_certs", "True")
    )
    try:
        _validate_handle_server_config(handle_config)
    except BindPIDException as err:
        logger.info(err)
        raise BindPIDsException
    for mdl in chain(
        [_get_sip(sip_uuid)], Directory.objects.filter(sip_id=sip_uuid).all()
    ):
        _bind_pid_to_model(job, mdl, shared_path, handle_config)


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sip_uuid",
        type=str,
        help="The UUID of the SIP to bind a PID for; any"
        " directories associated to this SIP will have"
        " PIDs bound as well.",
    )
    parser.add_argument(
        "shared_path", type=str, help="The shared directory where SIPs are stored."
    )

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])
                if args.sip_uuid == "None":
                    job.set_status(0)
                    continue

                logger.info("bind_pids called with args: %s", vars(args))
                job.set_status(main(job, **vars(args)))
