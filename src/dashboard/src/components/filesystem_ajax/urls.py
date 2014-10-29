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

from django.conf.urls import patterns
from django.conf import settings

urlpatterns = patterns('components.filesystem_ajax.views',
    (r'^download_ss/$', 'download_ss'),
    (r'^download_fs/$', 'download_fs'),
    (r'^contents/arrange/$', 'arrange_contents'),
    (r'^contents/$', 'contents'),
    (r'^children/location/(?P<location_uuid>' + settings.UUID_REGEX + ')/$', 'directory_children_proxy_to_storage_server'),
    (r'^delete/arrange/$', 'delete_arrange'),
    (r'^delete/$', 'delete'),
    (r'^move_within_arrange/$', 'move_within_arrange'),
    (r'^create_directory_within_arrange/$', 'create_directory_within_arrange'),
    (r'^copy_to_arrange/$', 'copy_to_arrange'),
    (r'^ransfer/$', 'start_transfer_logged_in'),
    (r'^copy_from_arrange/$', 'copy_from_arrange_to_completed'),
    (r'^copy_metadata_files/$', 'copy_metadata_files'),
)
