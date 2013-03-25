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

urlpatterns = patterns('components.ingest.views',
    (r'^$', 'ingest_grid'),
    (r'^(?P<uuid>' + settings.UUID_REGEX + ')/$', 'ingest_detail'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/delete/$', 'ingest_delete'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/$', 'ingest_metadata_list'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/add/$', 'ingest_metadata_edit'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/(?P<id>\d+)/$', 'ingest_metadata_edit'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/delete/(?P<id>\d+)/$', 'ingest_metadata_delete'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/microservices/$', 'ingest_microservices'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/$', 'ingest_upload'),
    (r'status/$', 'ingest_status'),
    (r'status/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'ingest_status'),
    (r'normalization-report/(?P<uuid>' + settings.UUID_REGEX + ')/(?P<current_page>\d+)/$', 'ingest_normalization_report'),
    (r'normalization-report/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'ingest_normalization_report'),
    (r'preview/aip/(?P<jobuuid>' + settings.UUID_REGEX + ')/$', 'ingest_browse_aip'),
    (r'preview/normalization/(?P<jobuuid>' + settings.UUID_REGEX + ')/$', 'ingest_browse_normalization')
)
