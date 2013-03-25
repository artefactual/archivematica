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

from django.conf.urls.defaults import patterns
from django.conf import settings

urlpatterns = patterns('components.archival_storage.views',
    (r'page/(?P<page>\d+)/$', 'archival_storage_page'),
    (r'search/json/file/(?P<document_id_modified>\w+)/$', 'archival_storage_file_json'),
    (r'search/$', 'archival_storage_search'),
    (r'download/aip/file/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'archival_storage_aip_file_download'),
    (r'download/aip/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'archival_storage_aip_download'),
    (r'thumbnail/(?P<fileuuid>' + settings.UUID_REGEX + ')/$', 'archival_storage_send_thumbnail'),
    (r'^$', 'archival_storage')
)
