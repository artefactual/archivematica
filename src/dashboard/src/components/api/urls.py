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
from components.api import views
from django.conf import settings
from django.urls import path
from django.urls import re_path

app_name = "api"
urlpatterns = [
    re_path(r"transfer/approve", views.approve_transfer, name="approve_transfer"),
    re_path(
        r"transfer/unapproved", views.unapproved_transfers, name="unapproved_transfers"
    ),
    re_path(
        r"transfer/completed", views.completed_transfers, name="completed_transfers"
    ),
    re_path(
        r"transfer/status/(?P<unit_uuid>" + settings.UUID_REGEX + ")",
        views.status,
        {"unit_type": "unitTransfer"},
        name="transfer_status",
    ),
    re_path(
        r"transfer/start_transfer/", views.start_transfer_api, name="start_transfer"
    ),
    re_path(
        r"transfer/reingest",
        views.reingest,
        {"target": "transfer"},
        name="transfer_reingest",
    ),
    re_path(
        r"ingest/status/(?P<unit_uuid>" + settings.UUID_REGEX + ")",
        views.status,
        {"unit_type": "unitSIP"},
        name="ingest_status",
    ),
    re_path(
        r"ingest/waiting", views.waiting_for_user_input, name="waiting_for_user_input"
    ),
    re_path(
        r"^(?P<unit_type>transfer|ingest)/(?P<unit_uuid>"
        + settings.UUID_REGEX
        + ")/delete/",
        views.mark_hidden,
        name="mark_hidden",
    ),
    re_path(
        r"^(?P<unit_type>transfer|ingest)/delete/",
        views.mark_completed_hidden,
        name="mark_completed_hidden",
    ),
    re_path(
        r"^ingest/reingest/approve", views.reingest_approve, name="reingest_approve"
    ),
    re_path(
        r"^ingest/reingest",
        views.reingest,
        {"target": "ingest"},
        name="ingest_reingest",
    ),
    re_path(r"^ingest/completed", views.completed_ingests, name="completed_ingests"),
    path("ingest/copy_metadata_files/", views.copy_metadata_files_api),
    path(
        "filesystem/administration/dips/atom/levels/",
        views.get_levels_of_description,
        name="get_levels_of_description",
    ),
    path(
        "administration/dips/atom/fetch_levels/",
        views.fetch_levels_of_description_from_atom,
        name="fetch_atom_lods",
    ),
    path("filesystem/metadata/", views.path_metadata, name="path_metadata"),
    re_path(
        r"processing-configuration/(?P<name>\w{1,16})",
        views.processing_configuration,
        name="processing_configuration",
    ),
    re_path(
        r"processing-configuration",
        views.processing_configurations,
        name="processing_configuration_list",
    ),
    re_path(r"v2beta/package", views.package),
    re_path(r"v2beta/validate/([-\w]+)", views.validate, name="v2beta_validate"),
    re_path(
        r"v2beta/jobs/(?P<unit_uuid>" + settings.UUID_REGEX + ")",
        views.unit_jobs,
        name="v2beta_jobs",
    ),
    re_path(
        r"v2beta/task/(?P<task_uuid>" + settings.UUID_REGEX + ")",
        views.task,
        name="v2beta_task",
    ),
]
