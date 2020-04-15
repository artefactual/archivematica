# -*- coding: utf-8 -*-
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
from __future__ import absolute_import

from django.urls import include, re_path
from django.conf import settings
from django.views.generic import TemplateView

from components.administration import views, views_dip_upload, views_processing


app_name = "administration"
urlpatterns = [
    re_path(r"^$", views.administration, name="administration_index"),
    re_path(
        r"reports/failures/delete/(?P<report_id>\w+)/$",
        views.failure_report_delete,
        name="failure_report_delete",
    ),
    re_path(
        r"reports/failures/(?P<report_id>\w+)/$",
        views.failure_report,
        name="failure_report",
    ),
    re_path(r"reports/failures/$", views.failure_report, name="reports_failures_index"),
    re_path(r"dips/as/$", views_dip_upload.admin_as, name="dips_as"),
    re_path(r"dips/atom/$", views_dip_upload.admin_atom, name="dips_atom_index"),
    re_path(
        r"dips/atom/edit_levels/$",
        views.atom_levels_of_description,
        name="atom_levels_of_description",
    ),
    re_path(
        r"^i18n/",
        include(("django.conf.urls.i18n", "django_i18n"), namespace="django_i18n"),
    ),
    re_path(
        r"language/$",
        TemplateView.as_view(template_name="administration/language.html"),
        name="admin_set_language",
    ),
    re_path(r"storage/$", views.storage, name="storage"),
    re_path(r"usage/$", views.usage, name="usage"),
    re_path(r"usage/clear/(?P<dir_id>\w+)/$", views.usage_clear, name="usage_clear"),
    re_path(r"processing/$", views_processing.list, name="processing"),
    re_path(r"processing/add/$", views_processing.edit, name="processing_add"),
    re_path(
        r"processing/edit/(?P<name>\w{1,16})/$",
        views_processing.edit,
        name="processing_edit",
    ),
    re_path(
        r"processing/reset/(?P<name>\w{1,16})/$",
        views_processing.reset,
        name="processing_reset",
    ),
    re_path(
        r"processing/delete/(?P<name>\w{1,16})/$",
        views_processing.delete,
        name="processing_delete",
    ),
    re_path(
        r"processing/download/(?P<name>\w{1,16})/$",
        views_processing.download,
        name="processing_download",
    ),
    re_path(r"premis/agent/$", views.premis_agent, name="premis_agent"),
    re_path(r"handle/$", views.handle_config, name="handle"),
    re_path(r"api/$", views.api, name="api"),
    re_path(r"general/$", views.general, name="general"),
    re_path(r"version/$", views.version, name="version"),
    re_path(
        r"taxonomy/term/(?P<term_uuid>" + settings.UUID_REGEX + ")/$",
        views.term_detail,
        name="term",
    ),
    re_path(
        r"taxonomy/term/(?P<term_uuid>" + settings.UUID_REGEX + ")/delete/$",
        views.term_delete,
    ),
    re_path(
        r"taxonomy/(?P<taxonomy_uuid>" + settings.UUID_REGEX + ")/$",
        views.terms,
        name="terms",
    ),
    re_path(r"taxonomy/$", views.taxonomy, name="taxonomy"),
]
