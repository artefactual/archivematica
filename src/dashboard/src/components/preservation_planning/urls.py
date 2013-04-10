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

urlpatterns = patterns('components.preservation_planning.views',
    #(r'fpr/(?P<current_page_number>\d+)/$', 'preservation_planning_fpr_data'),
    #(r'fpr/$', 'preservation_planning_fpr_data'),
    #(r'fpr/search/$', 'preservation_planning_fpr_search'),
    #(r'fpr/search/(?P<current_page_number>\d+)/$', 'preservation_planning_fpr_search'),
    #(r'$', 'preservation_planning')
    (r'old/$', 'preservation_planning'),
    (r'^(?P<uuid>' + settings.UUID_REGEX + ')/format/$', 'fpr_edit_format'),
    (r'^(?P<uuid>' + settings.UUID_REGEX + ')/command/$', 'fpr_edit_command'),
    (r'^(?P<uuid>' + settings.UUID_REGEX + ')/rule/$', 'fpr_edit_rule'),
    (r'rule/$', 'fpr_edit_rule'),
    (r'format/$', 'fpr_edit_format'),
    (r'command/$', 'fpr_edit_command'),
    (r'(?P<current_page_number>\d+)/$', 'preservation_planning_fpr_data'),
    (r'$', 'preservation_planning_fpr_data'),
    (r'search/$', 'preservation_planning_fpr_search'),
    (r'search/(?P<current_page_number>\d+)/$', 'preservation_planning_fpr_search')
)
