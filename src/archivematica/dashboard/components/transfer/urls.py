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
from components.transfer import views
from django.conf import settings
from django.urls import path
from django.urls import re_path

app_name = "transfer"
urlpatterns = [
    path("", views.grid, name="transfer_index"),
    # Transfer metadata set functions
    path("create_metadata_set_uuid/", views.create_metadata_set_uuid),
    re_path(
        r"^rename_metadata_set/(?P<set_uuid>"
        + settings.UUID_REGEX
        + r")/(?P<placeholder_id>[\w\-]+)/$",
        views.rename_metadata_set,
    ),
    re_path(
        r"^cleanup_metadata_set/(?P<set_uuid>" + settings.UUID_REGEX + ")/$",
        views.cleanup_metadata_set,
    ),
    path("locations/", views.transfer_source_locations),
    re_path(
        r"^component/(?P<uuid>" + settings.UUID_REGEX + ")/$",
        views.component,
        name="component",
    ),
    path("status/", views.status),
    re_path(r"^status/(?P<uuid>" + settings.UUID_REGEX + ")/$", views.status),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/metadata/$",
        views.transfer_metadata_list,
        name="transfer_metadata_list",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/metadata/add/$",
        views.transfer_metadata_edit,
        name="transfer_metadata_add",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + r")/metadata/(?P<id>\d+)/$",
        views.transfer_metadata_edit,
        name="transfer_metadata_edit",
    ),
]
