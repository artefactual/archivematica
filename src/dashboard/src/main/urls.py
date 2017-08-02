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

from django.conf.urls import include, url
from django.conf import settings

from main import views


urlpatterns = [
    # Index
    url(r'^$', views.home),

    # JavaScript i18n catalog
    url(r'^jsi18n/$', views.cached_javascript_catalog, {'domain': 'djangojs'}, name='javascript-catalog'),

    # Forbidden
    url(r'forbidden/$', views.forbidden),

    # Jobs and tasks (is part of ingest)
    url(r'tasks/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.tasks),
    url(r'task/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.task),

    # Access
    url(r'access/$', views.access_list),
    url(r'access/(?P<id>\d+)/delete/$', views.access_delete),

    # JSON feeds
    url(r'status/$', views.status),
    url(r'formdata/(?P<type>\w+)/(?P<parent_id>\d+)/(?P<delete_id>\d+)/$', views.formdata_delete),
    url(r'formdata/(?P<type>\w+)/(?P<parent_id>\d+)/$', views.formdata),

]

if 'shibboleth' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^shib/', include('shibboleth.urls', namespace='shibboleth')),
    ]
