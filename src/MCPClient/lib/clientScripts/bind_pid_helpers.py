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
from main.models import Identifier


class BindPIDsException(Exception):
    """If I am raised, return 1."""
    exit_code = 1


class BindPIDsWarning(Exception):
    """If I am raised, return 0."""
    exit_code = 0


def validate_handle_server_config(handle_config, logger=None):
    """While the handle server form is configured with required fields, the
    default form in Archivematica is blank which means the Bind PID service
    can fail if a user has selected to Bind PIDs without entering configuration
    values. Validate the configuration dictionary to handle this situation
    gracefully.
    """
    fields = [
        'resolve_url_template_archive',
        'resolve_url_template_file',
        'handle_resolver_url',
        'naming_authority',
        'pid_web_service_key',
        'pid_web_service_endpoint',
    ]
    for field in fields:
        try:
            handle_config[field]
        except KeyError:
            if logger:
                logger.warning("Handle server configuration is incomplete")
            return False
    return True


def _add_pid_to_mdl_identifiers(mdl, pid, purl):
    """Add a newly minted handle/PID to the ``SIP`` or ``Directory`` model as
    an identifier in its m2m ``identifiers`` attribute. Also add the PURL (URL
    constructed out of the PID) as a URI-type identifier.
    """
    hdl_identifier = Identifier.objects.create(type='hdl', value=pid)
    purl_identifier = Identifier.objects.create(type='URI', value=purl)
    mdl.identifiers.add(hdl_identifier)
    mdl.identifiers.add(purl_identifier)


def _add_custom_pid_to_mdl_identifiers(mdl, scheme, value):
    """Create an identifier with scheme:value and add the row to the
    Identifiers table. Reference the new identifier in the given model (mdl)
    table.
    """
    identifier = Identifier.objects.create(type=scheme, value=value)
    mdl.identifiers.add(identifier)
