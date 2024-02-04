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

var components;
var transferDirectoryPickerPathCounter = 1;

function createDirectoryPicker(locationUUID, baseDirectory, targetCssId, pathTemplateCssId, entryDisplayFilter) {
  var selector = new DirectoryPickerView({
    ajaxChildDataUrl: '/filesystem/children/location/' + locationUUID + '/',
    el: $('#explorer'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    entryDisplayFilter: entryDisplayFilter
  });

  var path_components = baseDirectory.replace(/\\/g,'/').split('/');
  var name = Base64.encode(path_components.pop()); // parse out path basename
  var parent = Base64.encode(path_components.join('/')); // parse out path directory
  if (path_components.length == 0) {
    // No leading / in baseDirectory, so parent is undefined to prevent leading /
    parent = undefined;
  }
  selector.structure = {
    'name': name,
    'parent': parent,
    'children': []
  };

  selector.pathTemplateRender = _.template($('#' + pathTemplateCssId).html());

  selector.options.actionHandlers = [{
    name: 'Select',
    description: gettext('Select'),
    iconHtml: 'Add',
    logic: function(result) {
      var decoded_path = Base64.decode(result.path)
      var trailing_slash = decoded_path + (result.type == 'directory' ? '/' : '');
      var location_path = locationUUID+':'+trailing_slash;

      if (components[location_path]) {
        alert(gettext("Error: The selected path is already present."));
        return;
      }

      // render path component
      $('#' + targetCssId).append(selector.pathTemplateRender({
        'path_counter': transferDirectoryPickerPathCounter,
        'path': decoded_path,
        'location_path': location_path,
        'edit_icon': '1',
        'delete_icon': '2'
      }));

      var component = {
        'path': location_path
      };
      components[location_path] = component;

      // activate edit and delete icons
      $('#' + pathTemplateCssId + '-' + transferDirectoryPickerPathCounter)
      .children('.transfer_path_icons')
      .children('.transfer_path_delete_icon')
      .click(function() {
        message = interpolate(gettext('Are you sure you want to remove %s?'), [$(this).parent().prev().text()]);
        if (confirm(message)) {
          var path = $(this).parent().prev().prop("id").trim();
          var component = components[path];

          delete components[path];
          $(this).parent().parent().remove();
        }
      });

      transferDirectoryPickerPathCounter++;

      // tiger stripe transfer paths
      $('.transfer_path').each(function() {
        $(this).parent().css('background-color', '');
      });
      $('.transfer_path:odd').each(function() {
        $(this).parent().css('background-color', '#eee');
      });
    }
  }];

  selector.render();
}
