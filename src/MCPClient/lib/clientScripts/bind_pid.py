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

"""Bind a PID to the input ``File`` model.

This client script binds a PID to a ``File`` model. This means making a single
request to a Handle web API endpoint to:

1. request that the file's UUID be registered as a handle (i.e., persistent
   identifier or PID), and
2. configure that PID/UUID-as-URL, i.e., PURL, to resolve to a base "resolve"
   URL and possibly also configure a number of qualified PURLs to resolve to
   related "resolve" URLs.

The idea is to allow for PURL resolution like:

    http://<PID-RESOLVER>/<NAME_AUTH>/<PID>
        => http://my-org-domain.org/access/files/<PID>
    http://<PID-RESOLVER>/<NAME_AUTH>/<PID>?locatt=view:preservation
        => http://my-org-domain.org/preservation/files/<PID>
    http://<PID-RESOLVER>/<NAME_AUTH>/<PID>?locatt=view:original
        => http://my-org-domain.org/original/files/<PID>

The sole command-line argument is the File's UUID. If the --bind-pids option
is something other than 'Yes', the script will exit without doing anything.
"""

import argparse
from functools import wraps

from django.db import transaction
import django

django.setup()
# dashboard
from main.models import DashboardSetting, File

# archivematicaCommon
import bindpid
from custom_handlers import get_script_logger
from archivematicaFunctions import str2bool


logger = get_script_logger("archivematica.mcp.client.bind_pid")


class BindPIDException(Exception):
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
        except BindPIDException as exc:
            return exc.exit_code

    return wrapped


def _get_bind_pid_config(file_uuid):
    """Return dict to pass to ``bindpid`` function as keyword arguments."""
    _args = {"entity_type": "file", "desired_pid": file_uuid}
    _args.update(DashboardSetting.objects.get_dict("handle"))
    bindpid._validate(_args)
    _args["pid_request_verify_certs"] = str2bool(
        _args.get("pid_request_verify_certs", "True")
    )
    return _args


def _update_file_mdl(file_uuid, naming_authority, resolver_url):
    """Add the newly minted handle to the ``File`` model as an identifier in its
    m2m ``identifiers`` attribute.
    """
    pid = "{}/{}".format(naming_authority, file_uuid)
    purl = "{}/{}".format(resolver_url.rstrip("/"), pid)
    file_mdl = File.objects.get(uuid=file_uuid)
    existing_ids = file_mdl.identifiers.all()
    for id_type, id_val in (("hdl", pid), ("URI", purl)):
        # Do not create duplicate identifiers. It is possible to create
        # duplicate ids because a user can ingest, and therefore bind a PID for,
        # a given file an arbitrary number of times. We allow this, in order to
        # allow changing the resolution of a PID, but there is no point in adding
        # redundant identifiers for the file.
        matches = [
            True for id_ in existing_ids if id_.type == id_type and id_.value == id_val
        ]
        if len(matches) == 0:
            file_mdl.add_custom_identifier(scheme=id_type, value=id_val)


@exit_on_known_exception
def main(job, file_uuid):
    """Bind the UUID ``file_uuid`` to the appropriate URL(s), given the
    configuration from the dashboard.
    """
    try:
        args = _get_bind_pid_config(file_uuid)
        msg = bindpid.bind_pid(**args)
        _update_file_mdl(
            file_uuid, args["naming_authority"], args["handle_resolver_url"]
        )
        job.print_output(
            msg
        )  # gets appended to handles.log file, cf. StandardTaskConfig
        logger.info(msg)
        return 0
    except bindpid.BindPIDException as exc:
        job.print_error(repr(exc))
        logger.info(exc)
        raise BindPIDException


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file_uuid", type=str, help="The UUID of the file to bind a PID for."
    )

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])
                if args.file_uuid == "None":
                    job.set_status(0)
                else:
                    logger.info("bind_pid called with args: %s", vars(args))
                    args = vars(args)
                    args["job"] = job
                    job.set_status(main(**(args)))
