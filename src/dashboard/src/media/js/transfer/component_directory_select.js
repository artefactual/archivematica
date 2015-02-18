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
var transferMetadataSetRowUUID;
var transferDirectoryPickerPathCounter = 1;

function createDirectoryPicker(locationUUID, baseDirectory, modalCssId, targetCssId, pathTemplateCssId, entryDisplayFilter) {
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
    description: 'Select',
    iconHtml: 'Add',
    logic: function(result) {
      // disable transfer type select as disk image transfer types
      // are displayed with a metadata editing option, but others
      // are not
      $('#transfer-type').attr('disabled', 'disabled');

      var decoded_path = Base64.decode(result.path)

      if (components[decoded_path]) {
        alert("Error: The selected path is already present in this transfer.");
        return;
      }

      // render path component
      var trailing_slash = decoded_path + (result.type == 'directory' ? '/' : '');
      var location_path = locationUUID+':'+trailing_slash;
      $('#' + targetCssId).append(selector.pathTemplateRender({
        'path_counter': transferDirectoryPickerPathCounter,
        'path': decoded_path,
        'location_path': location_path,
        'edit_icon': '1',
        'delete_icon': '2'
      }));

      if (!active_component) { active_component = createMetadataSetID(); }
      var component = active_component;
      component.path = location_path;
      components[location_path] = component;

      // enable editing of transfer component metadata
      if ($('#transfer-type').val() == 'disk image') {
        var $transferEditIconEl = $(
          '#' + pathTemplateCssId + '-' + transferDirectoryPickerPathCounter
        ).children('.transfer_path_icons').children('.transfer_path_edit_icon');

        $transferEditIconEl.click(function() {
          var component_metadata_url = '/transfer/component/' + component.uuid + '/';
          window.open(component_metadata_url, '_blank');
        });

        $transferEditIconEl.show();
      }

      active_component = undefined;

      // activate edit and delete icons
      $('#' + pathTemplateCssId + '-' + transferDirectoryPickerPathCounter)
      .children('.transfer_path_icons')
      .children('.transfer_path_delete_icon')
      .click(function() {
        if (confirm('Are you sure you want to remove this transfer component (' + $(this).parent().prev().text() + ')?')) {
          var path = $(this).parent().prev().prop("id").trim();
          var component = components[path];

          removeMetadataForms(component.uuid);

          delete components[path];
          $(this).parent().parent().remove();
          if ($('.transfer_path').length < 1) {
            // re-enable transfer type select
            $('#transfer-type').removeAttr('disabled');
          }
        }
      });

      transferDirectoryPickerPathCounter++;

      // remove directory picker
      $('#' + modalCssId).remove();

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
