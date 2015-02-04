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
import django.contrib.auth.views
from components.accounts import views

urlpatterns = patterns('',
    url(r'^$', views.list),
    url(r'add/$', views.add),
    url(r'(?P<id>\d+)/delete/$', views.delete),
    url(r'(?P<id>\d+)/edit/$', views.edit),
    url(r'profile/$', views.edit),
    url(r'list/$', views.list)
)

urlpatterns += patterns('',
    url(r'login/$', django.contrib.auth.views.login, { 'template_name': 'accounts/login.html' }),
    url(r'logout/$', django.contrib.auth.views.logout_then_login)
)
