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

from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    (r'^mcp/', include('components.mcp.urls')),
    (r'^installer/', include('installer.urls')),
    (r'^administration/accounts/', include('components.accounts.urls')),
    (r'^archival-storage/', include('components.archival_storage.urls')),
    (r'^preservation-planning/', include('components.preservation_planning.urls')),
    (r'transfer/(?P<uuid>' + settings.UUID_REGEX + ')/rights/', include('components.rights.transfer_urls')),
    (r'transfer/', include('components.transfer.urls')),
    (r'ingest/(?P<uuid>' + settings.UUID_REGEX + ')/rights/', include('components.rights.ingest_urls')),
    (r'ingest/', include('components.ingest.urls')),
    (r'^administration/', include('components.administration.urls')),
    (r'^filesystem/', include('components.filesystem_ajax.urls')),
    (r'^api/', include('components.api.urls')),
    (r'', include('main.urls'))
)
