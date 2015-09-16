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
from components.ingest import views
from components.ingest import views_atk
from components.ingest import views_as

urlpatterns = patterns('',
    url(r'^$', views.ingest_grid,
        name='ingest_index'),
    url(r'^aic/(?P<uuid>' + settings.UUID_REGEX + ')/metadata/add/$', views.aic_metadata_add),
    url(r'^(?P<uuid>' + settings.UUID_REGEX + ')/$', views.ingest_detail),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/delete/$', views.ingest_delete),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/$', views.ingest_metadata_list),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/add/$', views.ingest_metadata_edit),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/(?P<id>\d+)/$', views.ingest_metadata_edit),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/delete/(?P<id>\d+)/$', views.ingest_metadata_delete),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/event_detail/$', views.ingest_metadata_event_detail),
    url(r'(?P<sip_uuid>' + settings.UUID_REGEX + ')/metadata/add_files/$', views.ingest_metadata_add_files),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/microservices/$', views.ingest_microservices),
    url(r'upload/url/check/$', views.ingest_upload_destination_url_check),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/$', views.ingest_upload),
    url(r'status/$', views.ingest_status),
    url(r'status/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.ingest_status),
    url(r'normalization-report/(?P<uuid>' + settings.UUID_REGEX + ')/(?P<current_page>\d+)/$', views.ingest_normalization_report),
    url(r'normalization-report/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.ingest_normalization_report),
    url(r'preview/(?P<browse_type>[\w-]+)/(?P<jobuuid>' + settings.UUID_REGEX + ')/$', views.ingest_browse),
    url(r'backlog/file/download/(?P<uuid>' + settings.UUID_REGEX + ')/', views.transfer_file_download),
    url(r'backlog/$', views.transfer_backlog, {'ui': 'legacy'}),
    url(r'appraisal_list/$', views.transfer_backlog, {'ui': 'appraisal'}),
)

# Archivists Toolkit
urlpatterns += patterns('',
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/match/resource/(?P<resource_id>\d+)/$', views_atk.ingest_upload_atk_match_dip_objects_to_resource_levels),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/match/resourcecomponent/(?P<resource_component_id>\d+)/$', views_atk.ingest_upload_atk_match_dip_objects_to_resource_component_levels),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/resource/(?P<resource_id>\d+)/$', views_atk.ingest_upload_atk_resource),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/resourcecomponent/(?P<resource_component_id>\d+)/$', views_atk.ingest_upload_atk_resource_component),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/save/$', views_atk.ingest_upload_atk_save),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/reset/$', views_atk.ingest_upload_atk_reset),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/atk/$', views_atk.ingest_upload_atk)
)

# ArchivesSpace
urlpatterns = urlpatterns + patterns('components.ingest.views_as',
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/as/match/resource/(?P<resource_id>.+)/$', views_as.ingest_upload_as_match_dip_objects_to_resource_levels),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/as/match/resourcecomponent/(?P<resource_component_id>.+)/$', views_as.ingest_upload_as_match_dip_objects_to_resource_component_levels),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/as/resource/(?P<resource_id>.+)/$', views_as.ingest_upload_as_resource),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/as/resourcecomponent/(?P<resource_component_id>.+)/$', views_as.ingest_upload_as_resource_component),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/as/save/$', views_as.ingest_upload_as_save),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/as/match/$', views_as.ingest_upload_as_match),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/as/reset/$', views_as.ingest_upload_as_reset),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/as/review/$', views_as.ingest_upload_as_review_matches),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/upload/as/$', views_as.ingest_upload_as)
)
