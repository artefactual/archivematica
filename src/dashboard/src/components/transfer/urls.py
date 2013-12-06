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
from django.conf import settings

urlpatterns = patterns('components.transfer.views',
    (r'^$', 'grid'),

    # Transfer metadata set functions
    (r'^create_metadata_set_uuid/(?P<transfer_type>\w+)/$', 'create_metadata_set_uuid'),
    (r'^rename_metadata_set/(?P<set_uuid>' + settings.UUID_REGEX + ')/(?P<placeholder_id>[\w\-]+)/$', 'rename_metadata_set'),
    (r'^cleanup_metadata_set/(?P<set_uuid>' + settings.UUID_REGEX + ')/$', 'cleanup_metadata_set'),

    (r'component/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'component'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/$', 'detail'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/delete/$', 'delete'),
    (r'(?P<uuid>' + settings.UUID_REGEX + ')/microservices/$', 'microservices'),
    (r'status/$', 'status'),
    (r'status/(?P<uuid>' + settings.UUID_REGEX + ')/$', 'status'),
    (r'browser/$', 'browser'),
)
