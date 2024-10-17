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
from components.administration import views
from components.administration import views_dip_upload
from components.administration import views_processing
from components.administration.forms import ProcessingConfigurationForm
from django.conf import settings
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views.generic import TemplateView

app_name = "administration"
urlpatterns = [
    path("", views.administration, name="administration_index"),
    re_path(
        r"^reports/failures/delete/(?P<report_id>\w+)/$",
        views.failure_report_delete,
        name="failure_report_delete",
    ),
    re_path(
        r"^reports/failures/(?P<report_id>\w+)/$",
        views.failure_report,
        name="failure_report",
    ),
    path("reports/failures/", views.failure_report, name="reports_failures_index"),
    path("dips/as/", views_dip_upload.admin_as, name="dips_as"),
    path("dips/atom/", views_dip_upload.admin_atom, name="dips_atom_index"),
    path(
        "dips/atom/edit_levels/",
        views.atom_levels_of_description,
        name="atom_levels_of_description",
    ),
    path("i18n/", include(("django.conf.urls.i18n", "i18n"), namespace="i18n")),
    path(
        "language/",
        TemplateView.as_view(template_name="administration/language.html"),
        name="admin_set_language",
    ),
    path("storage/", views.storage, name="storage"),
    path("usage/", views.usage, name="usage"),
    re_path(r"^usage/clear/(?P<dir_id>\w+)/$", views.usage_clear, name="usage_clear"),
    path("processing/", views_processing.list, name="processing"),
    path("processing/add/", views_processing.edit, name="processing_add"),
    re_path(
        rf"^processing/edit/{ProcessingConfigurationForm.NAME_URL_REGEX}/$",
        views_processing.edit,
        name="processing_edit",
    ),
    re_path(
        rf"^processing/reset/{ProcessingConfigurationForm.NAME_URL_REGEX}/$",
        views_processing.reset,
        name="processing_reset",
    ),
    re_path(
        rf"^processing/delete/{ProcessingConfigurationForm.NAME_URL_REGEX}/$",
        views_processing.delete,
        name="processing_delete",
    ),
    re_path(
        rf"^processing/download/{ProcessingConfigurationForm.NAME_URL_REGEX}/$",
        views_processing.download,
        name="processing_download",
    ),
    path("premis/agent/", views.premis_agent, name="premis_agent"),
    path("handle/", views.handle_config, name="handle"),
    path("api/", views.api, name="api"),
    path("general/", views.general, name="general"),
    path("version/", views.version, name="version"),
    re_path(
        r"^taxonomy/term/(?P<term_uuid>" + settings.UUID_REGEX + ")/$",
        views.term_detail,
        name="term",
    ),
    re_path(
        r"^taxonomy/term/(?P<term_uuid>" + settings.UUID_REGEX + ")/delete/$",
        views.term_delete,
    ),
    re_path(
        r"^taxonomy/(?P<taxonomy_uuid>" + settings.UUID_REGEX + ")/$",
        views.terms,
        name="terms",
    ),
    path("taxonomy/", views.taxonomy, name="taxonomy"),
]
