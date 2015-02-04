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
from components.transfer import views

urlpatterns = patterns('',
    url(r'^$', views.grid),

    # Transfer metadata set functions
    url(r'^create_metadata_set_uuid/$', views.create_metadata_set_uuid),
    url(r'^rename_metadata_set/(?P<set_uuid>' + settings.UUID_REGEX + ')/(?P<placeholder_id>[\w\-]+)/$', views.rename_metadata_set),
    url(r'^cleanup_metadata_set/(?P<set_uuid>' + settings.UUID_REGEX + ')/$', views.cleanup_metadata_set),

    url(r'component/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.component),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/$', views.detail),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/delete/$', views.delete),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/microservices/$', views.microservices),
    url(r'status/$', views.status),
    url(r'status/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.status),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/$', views.transfer_metadata_list),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/add/$', views.transfer_metadata_edit),
    url(r'(?P<uuid>' + settings.UUID_REGEX + ')/metadata/(?P<id>\d+)/$', views.transfer_metadata_edit),
)
