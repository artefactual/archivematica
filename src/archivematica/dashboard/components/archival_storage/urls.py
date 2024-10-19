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
from components.archival_storage import views
from django.conf import settings
from django.urls import path
from django.urls import re_path

app_name = "archival_storage"
urlpatterns = [
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/$", views.view_aip, name="view_aip"
    ),
    re_path(
        r"^download/aip/file/(?P<uuid>" + settings.UUID_REGEX + ")/$",
        views.aip_file_download,
        name="aip_file_download",
    ),
    re_path(
        r"^download/aip/(?P<uuid>" + settings.UUID_REGEX + ")/mets_download/$",
        views.aip_mets_file_download,
        name="aip_mets_file_download",
    ),
    re_path(
        r"^download/aip/(?P<uuid>" + settings.UUID_REGEX + ")/pointer_file/$",
        views.aip_pointer_file_download,
        name="aip_pointer_file_download",
    ),
    re_path(
        r"^download/aip/(?P<uuid>" + settings.UUID_REGEX + ")/$",
        views.aip_download,
        name="aip_download",
    ),
    re_path(r"^search/json/file/(?P<document_id_modified>\w+)/$", views.file_json),
    path("search/create_aic/", views.create_aic, name="create_aic"),
    path("search/", views.search, name="archival_storage_search"),
    re_path(
        r"^thumbnail/(?P<fileuuid>" + settings.UUID_REGEX + ")/$", views.send_thumbnail
    ),
    re_path(r"^save_state/(?P<table>[-\w]+)/$", views.save_state, name="save_state"),
    re_path(r"^load_state/(?P<table>[-\w]+)/$", views.load_state, name="load_state"),
    path("", views.execute, name="archival_storage_index"),
]
