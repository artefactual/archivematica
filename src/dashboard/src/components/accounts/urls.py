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

urlpatterns = patterns('components.accounts.views',
    (r'^$', 'list'),
    (r'add/$', 'add'),
    (r'(?P<id>\d+)/delete/$', 'delete'),
    (r'(?P<id>\d+)/edit/$', 'edit'),
    (r'profile/$', 'edit'),
    (r'list/$', 'list')
)

urlpatterns += patterns('',
    (r'login/$', 'django.contrib.auth.views.login', { 'template_name': 'accounts/login.html' }),
    (r'logout/$', 'django.contrib.auth.views.logout_then_login')
)
