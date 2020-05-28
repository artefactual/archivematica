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

from django.conf.urls import url
from django.conf import settings

from components.archival_storage import views


app_name = "archival_storage"
urlpatterns = [
    url(r"^(?P<uuid>" + settings.UUID_REGEX + ")/$", views.view_aip, name="view_aip"),
    url(
        r"^download/aip/file/(?P<uuid>" + settings.UUID_REGEX + ")/$",
        views.aip_file_download,
        name="aip_file_download",
    ),
    url(
        r"^download/aip/(?P<uuid>" + settings.UUID_REGEX + ")/mets_download/$",
        views.aip_mets_file_download,
        name="aip_mets_file_download",
    ),
    url(
        r"^download/aip/(?P<uuid>" + settings.UUID_REGEX + ")/pointer_file/$",
        views.aip_pointer_file_download,
        name="aip_pointer_file_download",
    ),
    url(
        r"^download/aip/(?P<uuid>" + settings.UUID_REGEX + ")/$",
        views.aip_download,
        name="aip_download",
    ),
    url(r"^search/json/file/(?P<document_id_modified>\w+)/$", views.file_json),
    url(r"^search/create_aic/$", views.create_aic, name="create_aic"),
    url(r"^search/$", views.search, name="archival_storage_search"),
    url(
        r"^thumbnail/(?P<fileuuid>" + settings.UUID_REGEX + ")/$", views.send_thumbnail
    ),
    url(r"^save_state/(?P<table>[-\w]+)/$", views.save_state, name="save_state"),
    url(r"^load_state/(?P<table>[-\w]+)/$", views.load_state, name="load_state"),
    url(r"^$", views.execute, name="archival_storage_index"),
]
