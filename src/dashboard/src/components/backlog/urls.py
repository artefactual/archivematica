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
from components.backlog import views
from django.urls import path
from django.urls import re_path

app_name = "backlog"
urlpatterns = [
    path("", views.execute, name="backlog_index"),
    path("search/", views.search, name="backlog_search"),
    path(
        "delete/<uuid:uuid>/",
        views.delete,
        name="backlog_delete",
    ),
    path(
        "download/<uuid:uuid>/",
        views.download,
        name="backlog_download",
    ),
    re_path(r"save_state/(?P<table>[-\w]+)/$", views.save_state, name="save_state"),
    re_path(r"load_state/(?P<table>[-\w]+)/$", views.load_state, name="load_state"),
]
