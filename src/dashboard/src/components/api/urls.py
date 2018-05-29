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

from django.conf.urls import url
from django.conf import settings

from components.api import views

urlpatterns = [
    url(r'transfer/approve', views.approve_transfer),
    url(r'transfer/unapproved', views.unapproved_transfers),
    url(r'transfer/completed', views.completed_transfers),
    url(r'transfer/status/(?P<unit_uuid>' + settings.UUID_REGEX + ')', views.status, {'unit_type': 'unitTransfer'}),
    url(r'transfer/start_transfer/', views.start_transfer_api),
    url(r'transfer/reingest', views.reingest, {'target': 'transfer'}),

    url(r'ingest/status/(?P<unit_uuid>' + settings.UUID_REGEX + ')', views.status, {'unit_type': 'unitSIP'}),
    url(r'ingest/waiting', views.waiting_for_user_input),
    url(r'^(?P<unit_type>transfer|ingest)/(?P<unit_uuid>' + settings.UUID_REGEX + ')/delete/', views.mark_hidden),
    url(r'^(?P<unit_type>transfer|ingest)/delete/', views.mark_completed_hidden),

    url(r'^ingest/reingest/approve', views.reingest_approve),
    url(r'^ingest/reingest', views.reingest, {'target': 'ingest'}),
    url(r'^ingest/completed', views.completed_ingests),
    url(r'^ingest/copy_metadata_files/$', views.copy_metadata_files_api),

    url(r'administration/dips/atom/levels/$', views.get_levels_of_description),
    url(r'administration/dips/atom/fetch_levels/$', views.fetch_levels_of_description_from_atom, name='fetch_atom_lods'),
    url(r'filesystem/metadata/$', views.path_metadata),
    url(r'processing-configuration/(?P<name>\w{1,16})', views.processing_configuration, name='processing_configuration'),

    url(r'v2beta/package', views.package),
]
