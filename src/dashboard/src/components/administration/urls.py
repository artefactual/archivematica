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

from django.conf.urls import url, include
from django.conf import settings
from django.views.generic import TemplateView

from components.administration import views, views_dip_upload, views_processing
from components.administration.forms import ProcessingConfigurationForm


app_name = "administration"
urlpatterns = [
    url(r"^$", views.administration, name="administration_index"),
    url(
        r"reports/failures/delete/(?P<report_id>\w+)/$",
        views.failure_report_delete,
        name="failure_report_delete",
    ),
    url(
        r"reports/failures/(?P<report_id>\w+)/$",
        views.failure_report,
        name="failure_report",
    ),
    url(r"reports/failures/$", views.failure_report, name="reports_failures_index"),
    url(r"dips/as/$", views_dip_upload.admin_as, name="dips_as"),
    url(r"dips/atom/$", views_dip_upload.admin_atom, name="dips_atom_index"),
    url(
        r"dips/atom/edit_levels/$",
        views.atom_levels_of_description,
        name="atom_levels_of_description",
    ),
    url(r"^i18n/", include("django.conf.urls.i18n", namespace="django_i18n")),
    url(
        r"language/$",
        TemplateView.as_view(template_name="administration/language.html"),
        name="admin_set_language",
    ),
    url(r"storage/$", views.storage, name="storage"),
    url(r"usage/$", views.usage, name="usage"),
    url(r"usage/clear/(?P<dir_id>\w+)/$", views.usage_clear, name="usage_clear"),
    url(r"processing/$", views_processing.list, name="processing"),
    url(r"processing/add/$", views_processing.edit, name="processing_add"),
    url(
        r"processing/edit/{}/$".format(ProcessingConfigurationForm.NAME_URL_REGEX),
        views_processing.edit,
        name="processing_edit",
    ),
    url(
        r"processing/reset/{}/$".format(ProcessingConfigurationForm.NAME_URL_REGEX),
        views_processing.reset,
        name="processing_reset",
    ),
    url(
        r"processing/delete/{}/$".format(ProcessingConfigurationForm.NAME_URL_REGEX),
        views_processing.delete,
        name="processing_delete",
    ),
    url(
        r"processing/download/{}/$".format(ProcessingConfigurationForm.NAME_URL_REGEX),
        views_processing.download,
        name="processing_download",
    ),
    url(r"premis/agent/$", views.premis_agent, name="premis_agent"),
    url(r"handle/$", views.handle_config, name="handle"),
    url(r"api/$", views.api, name="api"),
    url(r"general/$", views.general, name="general"),
    url(r"version/$", views.version, name="version"),
    url(
        r"taxonomy/term/(?P<term_uuid>" + settings.UUID_REGEX + ")/$",
        views.term_detail,
        name="term",
    ),
    url(
        r"taxonomy/term/(?P<term_uuid>" + settings.UUID_REGEX + ")/delete/$",
        views.term_delete,
    ),
    url(
        r"taxonomy/(?P<taxonomy_uuid>" + settings.UUID_REGEX + ")/$",
        views.terms,
        name="terms",
    ),
    url(r"taxonomy/$", views.taxonomy, name="taxonomy"),
]
