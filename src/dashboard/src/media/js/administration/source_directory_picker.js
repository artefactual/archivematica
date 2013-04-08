/*
This file is part of Archivematica.

Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>

Archivematica is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Archivematica is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
*/

$(document).ready(function() {
  var ajaxChildDataUrl = '/filesystem/children/'
    , ajaxSelectedDirectoryUrl = '/administration/sources/json/'
    , ajaxAddDirectoryUrl = '/administration/sources/json/'
    , ajaxDeleteDirectoryUrl = '/administration/sources/delete/json/'
    , picker = new DirectoryPickerView({
      el:               $('#explorer'),
      levelTemplate:    $('#template-dir-level').html(),
      entryTemplate:    $('#template-dir-entry').html(),
      ajaxChildDataUrl: ajaxChildDataUrl,
      ajaxSelectedDirectoryUrl: ajaxSelectedDirectoryUrl,
      ajaxAddDirectoryUrl: ajaxAddDirectoryUrl,
      ajaxDeleteDirectoryUrl: ajaxDeleteDirectoryUrl
  });

  picker.structure = {
    'name': 'home',
    'parent': '',
    'children': []
  };

  picker.render();
  picker.updateSelectedDirectories();
});
