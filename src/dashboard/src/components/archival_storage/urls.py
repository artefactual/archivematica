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

from django.conf.urls import url, patterns
from django.conf import settings
from components.archival_storage import views

urlpatterns = patterns('',
    url(r'search/json/file/(?P<document_id_modified>\w+)/$', views.file_json),
    url(r'search/json/aip/(?P<document_id_modified>\w+)/$', views.aip_json),
    url(r'search/create_aic/$', views.create_aic,
        name='create_aic'),
    url(r'search/$', views.search,
        name='archival_storage_search'),
    url(r'delete/aip/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.aip_delete,
        name='aip_delete'),
    url(r'(?P<package_uuid>' + settings.UUID_REGEX + ')/reingest/$', views.reingest_aip,
        name='reingest_aip'),
    url(r'download/aip/file/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.aip_file_download),
    url(r'download/aip/(?P<uuid>' + settings.UUID_REGEX + ')/pointer_file/$', views.aip_pointer_file_download),
    url(r'download/aip/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.aip_download),
    url(r'thumbnail/(?P<fileuuid>' + settings.UUID_REGEX + ')/$', views.send_thumbnail),
    url(r'^$', views.overview,
        name='archival_storage_index')
)
