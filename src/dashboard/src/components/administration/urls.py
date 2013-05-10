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
    (r'dip/edit/(?P<id>' + settings.UUID_REGEX + ')/$', 'dip_edit'),
    (r'dips/atom/$', 'atom_dips'),
    (r'dips/contentdm/$', 'contentdm_dips'),
    (r'sources/$', 'sources'),
    (r'sources/delete/json/(?P<id>' + settings.UUID_REGEX + ')/$', 'sources_delete_json'),
    (r'storage/delete/json/(?P<id>' + settings.UUID_REGEX + ')/$', 'storage_delete_json'),
    (r'storage/$', 'storage'),
    (r'processing/$', 'processing'),
    (r'sources/json/$', 'sources_json'),
    (r'storage/json/$', 'storage_json'),
    (r'premis/agent/$', 'premis_agent'),
    (r'api/$', 'api')
)
