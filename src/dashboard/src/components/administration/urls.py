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
from components.administration import views

urlpatterns = patterns('',
    url(r'^$', views.administration),
    url(r'reports/failures/delete/(?P<report_id>\w+)/$', views.failure_report_delete),
    url(r'reports/failures/(?P<report_id>\w+)/$', views.failure_report),
    url(r'reports/failures/$', views.failure_report),
    url(r'dips/as/$', views.administration_as_dips),
    url(r'dips/atk/$', views.administration_atk_dips),
    url(r'dips/atom/$', views.atom_dips),
    url(r'dips/atom/edit_levels/$', views.atom_levels_of_description),
    url(r'sources/$', views.sources),
    url(r'storage/$', views.storage),
    url(r'usage/$', views.usage),
    url(r'usage/clear/(?P<dir_id>\w+)/$', views.usage_clear),
    url(r'processing/$', views.processing),
    url(r'premis/agent/$', views.premis_agent),
    url(r'api/$', views.api),
    url(r'general/$', views.general),
    url(r'version/$', views.version),
    url(r'taxonomy/term/(?P<term_uuid>' + settings.UUID_REGEX + ')/$', views.term_detail),
    url(r'taxonomy/term/(?P<term_uuid>' + settings.UUID_REGEX + ')/delete/$', views.term_delete),
    url(r'taxonomy/(?P<taxonomy_uuid>' + settings.UUID_REGEX + ')/$', views.terms),
    url(r'taxonomy/$', views.taxonomy),
)
