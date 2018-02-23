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

from django.conf.urls import url
from django.conf import settings
from components.filesystem_ajax import views

urlpatterns = [
    url(r'^download_ss/$', views.download_ss),
    url(r'^download_fs/$', views.download_fs),
    url(r'^(?P<uuid>' + settings.UUID_REGEX + ')/download/$', views.download_by_uuid),
    url(r'^(?P<uuid>' + settings.UUID_REGEX + ')/preview/$', views.preview_by_uuid),
    url(r'^contents/arrange/$', views.arrange_contents),
    url(r'^contents/$', views.contents),
    url(r'^children/location/(?P<location_uuid>' + settings.UUID_REGEX + ')/$', views.directory_children_proxy_to_storage_server),
    url(r'^delete/arrange/$', views.delete_arrange),
    url(r'^create_directory_within_arrange/$', views.create_directory_within_arrange),
    url(r'^copy_to_arrange/$', views.copy_to_arrange),
    url(r'^copy_from_arrange/$', views.copy_from_arrange_to_completed),
    url(r'^copy_metadata_files/$', views.copy_metadata_files_logged_in),
]
