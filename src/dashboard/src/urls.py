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

from django.conf.urls import url, include, patterns
from django.conf import settings

urlpatterns = patterns('',
    url(r'^mcp/', include('components.mcp.urls')),
    url(r'^installer/', include('installer.urls')),
    url(r'^administration/accounts/', include('components.accounts.urls')),
    url(r'^archival-storage/', include('components.archival_storage.urls')),
    url(r'^fpr/', include('fpr.urls')),
    url(r'^transfer/(?P<uuid>' + settings.UUID_REGEX + ')/rights/', include('components.rights.transfer_urls')),
    url(r'^transfer/', include('components.transfer.urls')),
    url(r'^appraisal/', include('components.appraisal.urls')),
    url(r'^ingest/(?P<uuid>' + settings.UUID_REGEX + ')/rights/', include('components.rights.ingest_urls')),
    url(r'^ingest/', include('components.ingest.urls')),
    url(r'^administration/', include('components.administration.urls')),
    url(r'^filesystem/', include('components.filesystem_ajax.urls')),
    url(r'^api/', include('components.api.urls')),
    url(r'^file/', include('components.file.urls')),
    url(r'^access/', include('components.access.urls')),
    url(r'', include('main.urls'))
)
