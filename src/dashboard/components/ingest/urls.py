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
from components.ingest import views
from components.ingest import views_as
from django.conf import settings
from django.urls import path
from django.urls import re_path

app_name = "ingest"
urlpatterns = [
    path("", views.ingest_grid, name="ingest_index"),
    path("sips/", views.SipsView.as_view()),
    re_path(
        r"^aic/(?P<uuid>" + settings.UUID_REGEX + ")/metadata/add/$",
        views.aic_metadata_add,
        name="aic_metadata_add",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/metadata/$",
        views.ingest_metadata_list,
        name="ingest_metadata_list",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/metadata/add/$",
        views.ingest_metadata_edit,
        name="ingest_metadata_add",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + r")/metadata/(?P<id>\d+)/$",
        views.ingest_metadata_edit,
        name="ingest_metadata_edit",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + r")/metadata/delete/(?P<id>\d+)/$",
        views.ingest_metadata_delete,
        name="ingest_metadata_delete",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/metadata/event_detail/$",
        views.ingest_metadata_event_detail,
        name="ingest_metadata_event_detail",
    ),
    re_path(
        r"^(?P<sip_uuid>" + settings.UUID_REGEX + ")/metadata/add_files/$",
        views.ingest_metadata_add_files,
        name="ingest_metadata_add_files",
    ),
    path("upload/url/check/", views.ingest_upload_destination_url_check),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/upload/$",
        views.ingest_upload,
        name="ingest_upload",
    ),
    path("status/", views.ingest_status),
    re_path(r"^status/(?P<uuid>" + settings.UUID_REGEX + ")/$", views.ingest_status),
    re_path(
        r"^normalization-report/(?P<uuid>"
        + settings.UUID_REGEX
        + r")/(?P<current_page>\d+)/$",
        views.ingest_normalization_report,
        name="ingest_normalization_report_page",
    ),
    re_path(
        r"^normalization-report/(?P<uuid>" + settings.UUID_REGEX + ")/$",
        views.ingest_normalization_report,
        name="ingest_normalization_report",
    ),
    re_path(
        r"^preview/(?P<browse_type>[\w-]+)/(?P<jobuuid>" + settings.UUID_REGEX + ")/$",
        views.ingest_browse,
    ),
    re_path(
        r"^backlog/file/download/(?P<uuid>" + settings.UUID_REGEX + ")/",
        views.transfer_file_download,
    ),
    path("backlog/", views.transfer_backlog, {"ui": "legacy"}),
    path("appraisal_list/", views.transfer_backlog, {"ui": "appraisal"}),
]

# ArchivesSpace
urlpatterns += [
    re_path(
        r"^(?P<uuid>"
        + settings.UUID_REGEX
        + ")/upload/as/match/resource/(?P<resource_id>.+)/$",
        views_as.ingest_upload_as_match_dip_objects_to_resource_levels,
        name="ingest_upload_as_match_dip_objects_to_resource_levels",
    ),
    re_path(
        r"^(?P<uuid>"
        + settings.UUID_REGEX
        + ")/upload/as/match/resourcecomponent/(?P<resource_component_id>.+)/$",
        views_as.ingest_upload_as_match_dip_objects_to_resource_component_levels,
        name="ingest_upload_as_match_dip_objects_to_resource_component_levels",
    ),
    re_path(
        r"^(?P<uuid>"
        + settings.UUID_REGEX
        + ")/upload/as/resource/(?P<resource_id>.+)/$",
        views_as.ingest_upload_as_resource,
        name="ingest_upload_as_resource",
    ),
    re_path(
        r"^(?P<uuid>"
        + settings.UUID_REGEX
        + ")/upload/as/resourcecomponent/(?P<resource_component_id>.+)/$",
        views_as.ingest_upload_as_resource_component,
        name="ingest_upload_as_resource_component",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/upload/as/save/$",
        views_as.ingest_upload_as_save,
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/upload/as/match/$",
        views_as.ingest_upload_as_match,
        name="ingest_upload_as_match",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/upload/as/reset/$",
        views_as.ingest_upload_as_reset,
        name="ingest_upload_as_reset",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/upload/as/review/$",
        views_as.ingest_upload_as_review_matches,
        name="ingest_upload_as_review_matches",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/upload/as/complete/$",
        views_as.complete_matching,
        name="complete_matching",
    ),
    re_path(
        r"^(?P<uuid>" + settings.UUID_REGEX + ")/upload/as/$",
        views_as.ingest_upload_as,
        name="ingest_upload_as",
    ),
]
