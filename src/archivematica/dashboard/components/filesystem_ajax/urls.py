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
from django.conf import settings
from django.urls import path
from django.urls import re_path

from archivematica.dashboard.components.filesystem_ajax import views

app_name = "filesystem_ajax"
urlpatterns = [
    path("download_ss/", views.download_ss),
    path("download_fs/", views.download_fs),
    path("contents/", views.contents, name="contents"),
    re_path(
        r"^children/location/(?P<location_uuid>" + settings.UUID_REGEX + ")/$",
        views.directory_children_proxy_to_storage_server,
    ),
    path("copy_metadata_files/", views.copy_metadata_files, name="copy_metadata_files"),
]
