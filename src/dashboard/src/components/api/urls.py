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

from components.api import views

urlpatterns = patterns('',
    url(r'transfer/approve', views.approve_transfer),
    url(r'transfer/unapproved', views.unapproved_transfers),
    url(r'transfer/status/(?P<unit_uuid>' + settings.UUID_REGEX + ')', views.status, {'unit_type': 'unitTransfer'}),
    url(r'transfer/start_transfer/', views.start_transfer_api),
    url(r'ingest/status/(?P<unit_uuid>' + settings.UUID_REGEX + ')', views.status, {'unit_type': 'unitSIP'}),
    url(r'ingest/waiting', views.waiting_for_user_input),

    url(r'^ingest/reingest', views.start_reingest),

    url(r'administration/dips/atom/levels/$', views.get_levels_of_description),
    url(r'administration/dips/atom/fetch_levels/$', views.fetch_levels_of_description_from_atom),
    url(r'filesystem/metadata/$', views.path_metadata),
)
