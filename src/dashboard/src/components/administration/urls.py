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

from django.conf.urls.defaults import patterns
from django.conf import settings

urlpatterns = patterns('components.administration.views',
    (r'^$', 'administration'),
    #(r'edit/(?P<id>\d+)/$', 'administration_edit'),
    (r'dip/$', 'administration_dip'),
    (r'dip/edit/(?P<id>' + settings.UUID_REGEX + ')/$', 'administration_dip_edit'),
    (r'dips/atom/$', 'administration_atom_dips'),
    (r'dips/contentdm/$', 'administration_contentdm_dips'),
    (r'sources/$', 'administration_sources'),
    (r'sources/delete/json/(?P<id>' + settings.UUID_REGEX + ')/$', 'administration_sources_delete_json'),
    (r'storage/delete/json/(?P<id>' + settings.UUID_REGEX + ')/$', 'administration_storage_delete_json'),
    (r'storage/$', 'administration_storage'),
    (r'processing/$', 'administration_processing'),
    (r'sources/json/$', 'administration_sources_json'),
    (r'storage/json/$', 'administration_storage_json'),
    (r'premis/agent/$', 'administration_premis_agent'),
    (r'api/$', 'administration_api')
)
