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

urlpatterns = patterns('components.rights.views',
    (r'^$', 'ingest_rights_list'),
    (r'add/$', 'ingest_rights_edit'),
    (r'delete/(?P<id>\d+)/$', 'ingest_rights_delete'),
    (r'grants/(?P<id>\d+)/delete/$', 'ingest_rights_grant_delete'),
    (r'grants/(?P<id>\d+)/$', 'ingest_rights_grants_edit'),
    (r'(?P<id>\d+)/$', 'ingest_rights_edit')
)
