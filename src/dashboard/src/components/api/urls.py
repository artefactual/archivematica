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

from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('components.api.views',
    (r'transfer/approve', 'approve_transfer'), 
    (r'transfer/unapproved', 'unapproved_transfers'),
    url(r'transfer/status/(?P<unit_uuid>' + settings.UUID_REGEX + ')', 'status', {'unit_type': 'unitTransfer'}),
    url(r'transfer/start_transfer/', 'start_transfer_api'),
    url(r'ingest/status/(?P<unit_uuid>' + settings.UUID_REGEX + ')', 'status', {'unit_type': 'unitSIP'}),
    (r'ingest/waiting', 'waiting_for_user_input'),
)
