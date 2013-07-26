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

var transferMetadataSetRowUUID = false,
    transferDirectoryPickerPathCounter = 1;

function createDirectoryPicker(baseDirectory, modalCssId, targetCssId, pathTemplateCssId) {
  var selector = new DirectoryPickerView({
    ajaxChildDataUrl: '/filesystem/children/location/' + locationUUID + '/',
    el: $('#explorer'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html()
  });

  selector.structure = {
    'name': baseDirectory.replace(/\\/g,'/').replace( /.*\//, '' ),      // parse out path basename
    'parent': baseDirectory.replace(/\\/g,'/').replace(/\/[^\/]*$/, ''), // parse out path directory
    'children': []
  };

  selector.pathTemplateRender = _.template($('#' + pathTemplateCssId).html());

  selector.options.entryDisplayFilter = function(entry) {
    // if a file and not an archive file, then hide
    if (
      entry.children == undefined
      && entry.attributes.name.toLowerCase().indexOf('.zip') == -1
      && entry.attributes.name.toLowerCase().indexOf('.tgz') == -1
      && entry.attributes.name.toLowerCase().indexOf('.tar.gz') == -1
    ) {
        return false;
    }
    return true;
  };

  selector.options.actionHandlers = [{
    name: 'Select',
    description: 'Select',
    iconHtml: 'Add',
    logic: function(result) {
      // A global variable is used to track the current transfer metadata
      // set ID.
      //
      // If a transfer metadata set hasn't been created, create one via a 
      // synchronous AJAX request.
      if (transferMetadataSetRowUUID == false) {
        var transferTypeNormalized = $('#transfer-type').val().replace(' ', '_');
        $.ajax({
          'url': '/filesystem/get_transfer_metadata_set/' + transferTypeNormalized + '/',
          'type': 'GET',
          'async': false,
          'cache': false,
          'success': function(results) {
             transferMetadataSetRowUUID = results.uuid;
          },
          'error': function() {
            alert('Error: contact administrator.');
          }
        });

        // disable transfer type select as disk image transfer types
        // are displayed with a metadata editing option, but others
        // are not
        $('#transfer-type').attr('disabled', 'disabled');
      }

      // render path component
      $('#' + targetCssId).append(selector.pathTemplateRender({
        'path_counter': transferDirectoryPickerPathCounter,
        'path': result.path,
        'edit_icon': '1',
        'delete_icon': '2'
      }));

      // enable editing of transfer component metadata
      if ($('#transfer-type').val() == 'disk image') {
        var $transferEditIconEl =  $(
          '#' + pathTemplateCssId + '-' + transferDirectoryPickerPathCounter
        ).children('.transfer_path_edit_icon');

        $transferEditIconEl.click(function() {
          var path = $(this).parent().children('.transfer_path').text(),
              component_metadata_url = '/transfer/component/' + transferMetadataSetRowUUID + '/?path=' + encodeURIComponent(path);
          window.open(component_metadata_url, '_blank');
        });

        $transferEditIconEl.show();
      }

      // activate edit and delete icons
      $('#' + pathTemplateCssId + '-' + transferDirectoryPickerPathCounter).children('.transfer_path_delete_icon').click(function() {
        $(this).parent().remove();
        if ($('.transfer_path').length < 1) {
          // re-enable transfer type select
          $('#transfer-type').removeAttr('disabled');
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
