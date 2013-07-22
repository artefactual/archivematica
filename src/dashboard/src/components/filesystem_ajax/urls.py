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
    (r'^download/$', 'download'),
    (r'^contents/$', 'contents'),
    (r'^children/location/(?P<location_uuid>' + settings.UUID_REGEX + ')/$', 'directory_children_proxy_to_storage_server'),
    #(r'^children/$', 'directory_children'),

    (r'^delete/$', 'delete'),
    (r'^copy_to_originals/$', 'copy_to_originals'),
    (r'^copy_to_arrange/$', 'copy_to_arrange'),
    (r'^copy_transfer_component/$', 'copy_transfer_component'),
    (r'^get_temp_directory/$', 'get_temp_directory'),
    (r'^get_transfer_metadata_set/(?P<transfer_type>\w+)/$', 'get_transfer_metadata_set'),
    (r'^ransfer/$', 'copy_to_start_transfer'),
    (r'^copy_from_arrange/$', 'copy_from_arrange_to_completed')
)
