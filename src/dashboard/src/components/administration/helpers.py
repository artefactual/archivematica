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

from components import helpers

def hidden_sections():
    hide_sections = {}

    short_forms = {
      'atom_dip':      'dashboard_administration_atom_dip_enabled',
      'contentdm_dip': 'dashboard_administration_contentdm_dip_enabled'
    }

    for short_form, long_form in short_forms.items():
        hide_sections[short_form] = helpers.get_boolean_setting(long_form)

    return hide_sections
