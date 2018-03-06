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

from django.conf.urls import url, include
from django.conf import settings
from django.views.generic import TemplateView

from components.administration import views, views_dip_upload, views_processing


urlpatterns = [
    url(r'^$', views.administration),
    url(r'reports/failures/delete/(?P<report_id>\w+)/$', views.failure_report_delete),
    url(r'reports/failures/(?P<report_id>\w+)/$', views.failure_report),
    url(r'reports/failures/$', views.failure_report),
    url(r'dips/as/$', views_dip_upload.admin_as),
    url(r'dips/atk/$', views_dip_upload.admin_atk),
    url(r'dips/atom/$', views_dip_upload.admin_atom),
    url(r'dips/atom/edit_levels/$', views.atom_levels_of_description),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'language/$', TemplateView.as_view(template_name='administration/language.html'), name='admin_set_language'),
    url(r'sources/$', views.sources),
    url(r'storage/$', views.storage),
    url(r'usage/$', views.usage),
    url(r'usage/clear/(?P<dir_id>\w+)/$', views.usage_clear),
    url(r'processing/$', views_processing.list),
    url(r'processing/add/$', views_processing.edit),
    url(r'processing/edit/(?P<name>\w{1,16})/$', views_processing.edit),
    url(r'processing/reset/(?P<name>\w{1,16})/$', views_processing.reset),
    url(r'processing/delete/(?P<name>\w{1,16})/$', views_processing.delete),
    url(r'processing/download/(?P<name>\w{1,16})/$', views_processing.download),
    url(r'premis/agent/$', views.premis_agent),
    url(r'handle/$', views.handle_config),
    url(r'api/$', views.api),
    url(r'general/$', views.general),
    url(r'version/$', views.version),
    url(r'taxonomy/term/(?P<term_uuid>' + settings.UUID_REGEX + ')/$', views.term_detail),
    url(r'taxonomy/term/(?P<term_uuid>' + settings.UUID_REGEX + ')/delete/$', views.term_delete),
    url(r'taxonomy/(?P<taxonomy_uuid>' + settings.UUID_REGEX + ')/$', views.terms),
    url(r'taxonomy/$', views.taxonomy),
]
