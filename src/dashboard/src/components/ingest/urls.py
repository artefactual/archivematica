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

from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('components.ingest.views',
    url(r'^$', 'ingest_grid',
        name='ingest_index'),
    url(r'^aic/(?P<uuid>' + settings.UUID_REGEX + ')/metadata/add/$', 'aic_metadata_add'),
    url(r'^(?P<uuid>' + settings.UUID_REGEX + ')/$', 'ingest_detail'),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/delete/$', 'ingest_delete'),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/$', 'ingest_metadata_list'),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/add/$', 'ingest_metadata_edit'),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/(?P<id>\d+)/$', 'ingest_metadata_edit'),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/delete/(?P<id>\d+)/$', 'ingest_metadata_delete'),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/event_detail/$', 'ingest_metadata_event_detail'),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/microservices/$', 'ingest_microservices'),
    url(r'upload/url/check/$', 'ingest_upload_destination_url_check'),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/$', 'ingest_upload'),
    url(r'status/$', 'ingest_status'),
    url(r'status/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'ingest_status'),
    url(r'normalization-report/(?P<uuid>' + settings.UUID_REGEX + ')/(?P<current_page>\d+)/$', 'ingest_normalization_report'),
    url(r'normalization-report/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'ingest_normalization_report'),
    url(r'preview/aip/(?P<jobuuid>' + settings.UUID_REGEX + ')/$', 'ingest_browse_aip'),
    url(r'preview/normalization/(?P<jobuuid>' + settings.UUID_REGEX + ')/$', 'ingest_browse_normalization'),
    url(r'backlog/file/download/(?P<uuid>' + settings.UUID_REGEX + ')/', 'transfer_file_download'),
    url(r'backlog/$', 'transfer_backlog')
)

urlpatterns = urlpatterns + patterns('components.ingest.views_atk',
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/match/resource/(?P<resource_id>\d+)/$', 'ingest_upload_atk_match_dip_objects_to_resource_levels'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/match/resourcecomponent/(?P<resource_component_id>\d+)/$', 'ingest_upload_atk_match_dip_objects_to_resource_component_levels'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/resource/(?P<resource_id>\d+)/$', 'ingest_upload_atk_resource'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/resourcecomponent/(?P<resource_component_id>\d+)/$', 'ingest_upload_atk_resource_component'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/save/$', 'ingest_upload_atk_save'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/$', 'ingest_upload_atk')
)
