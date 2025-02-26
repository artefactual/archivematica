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
from main import views

app_name = "main"
urlpatterns = [
    # Index
    path("", views.home, name="main_index"),
    # JavaScript i18n catalog
    path(
        "jsi18n/",
        views.cached_javascript_catalog,
        {"domain": "djangojs"},
        name="javascript-catalog",
    ),
    # Forbidden
    path("forbidden/", views.forbidden, name="forbidden"),
    # Jobs and tasks (is part of ingest)
    re_path(r"tasks/(?P<uuid>" + settings.UUID_REGEX + ")/$", views.tasks),
    re_path(r"task/(?P<uuid>" + settings.UUID_REGEX + ")/$", views.task, name="task"),
    # Access
    path("access/", views.access_list, name="access_index"),
    path("access/<int:id>/delete/", views.access_delete, name="access_delete"),
    # JSON feeds
    path("status/", views.status),
    re_path(
        r"formdata/(?P<type>\w+)/(?P<parent_id>\d+)/(?P<delete_id>\d+)/$",
        views.formdata_delete,
    ),
    re_path(r"formdata/(?P<type>\w+)/(?P<parent_id>\d+)/$", views.formdata),
]
