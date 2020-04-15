# -*- coding: utf-8 -*-
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import

from django.urls import re_path
from django.conf import settings

from components.api import views

app_name = "api"
urlpatterns = [
    re_path(r"transfer/approve", views.approve_transfer),
    re_path(r"transfer/unapproved", views.unapproved_transfers),
    re_path(r"transfer/completed", views.completed_transfers),
    re_path(
        r"transfer/status/(?P<unit_uuid>" + settings.UUID_REGEX + ")",
        views.status,
        {"unit_type": "unitTransfer"},
    ),
    re_path(r"transfer/start_transfer/", views.start_transfer_api),
    re_path(r"transfer/reingest", views.reingest, {"target": "transfer"}),
    re_path(
        r"ingest/status/(?P<unit_uuid>" + settings.UUID_REGEX + ")",
        views.status,
        {"unit_type": "unitSIP"},
    ),
    re_path(r"ingest/waiting", views.waiting_for_user_input),
    re_path(
        r"^(?P<unit_type>transfer|ingest)/(?P<unit_uuid>"
        + settings.UUID_REGEX
        + ")/delete/",
        views.mark_hidden,
    ),
    re_path(r"^(?P<unit_type>transfer|ingest)/delete/", views.mark_completed_hidden),
    re_path(r"^ingest/reingest/approve", views.reingest_approve),
    re_path(r"^ingest/reingest", views.reingest, {"target": "ingest"}),
    re_path(r"^ingest/completed", views.completed_ingests),
    re_path(r"^ingest/copy_metadata_files/$", views.copy_metadata_files_api),
    re_path(r"administration/dips/atom/levels/$", views.get_levels_of_description),
    re_path(
        r"administration/dips/atom/fetch_levels/$",
        views.fetch_levels_of_description_from_atom,
        name="fetch_atom_lods",
    ),
    re_path(r"filesystem/metadata/$", views.path_metadata),
    re_path(
        r"processing-configuration/(?P<name>\w{1,16})",
        views.processing_configuration,
        name="processing_configuration",
    ),
    re_path(r"v2beta/package", views.package),
    re_path(r"v2beta/validate/([-\w]+)", views.validate, name="validate"),
    re_path(r"v2beta/jobs/(?P<unit_uuid>" + settings.UUID_REGEX + ")", views.unit_jobs),
    re_path(r"v2beta/task/(?P<task_uuid>" + settings.UUID_REGEX + ")", views.task),
]
