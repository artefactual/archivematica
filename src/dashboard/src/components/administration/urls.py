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

from django.conf.urls import patterns

urlpatterns = patterns('components.administration.views',
    (r'^$', 'administration'),
    (r'reports/failures/delete/(?P<report_id>\w+)/$', 'failure_report_delete'),
    (r'reports/failures/(?P<report_id>\w+)/$', 'failure_report'),
    (r'reports/failures/$', 'failure_report'),
    (r'dips/atk/$', 'administration_atk_dips'),
    (r'dips/atom/$', 'atom_dips'),
    (r'dips/contentdm/$', 'contentdm_dips'),
    (r'sources/$', 'sources'),
    (r'storage/$', 'storage'),
    (r'processing/$', 'processing'),
    (r'premis/agent/$', 'premis_agent'),
    (r'api/$', 'api'),
    (r'general/$', 'general'),
    (r'version/$', 'version'),
)
