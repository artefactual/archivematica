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

var transferMetadataSetRowId = false;

function createDirectoryPicker(baseDirectory, modalCssId, targetCssId, locationUUID) {
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
      if (transferMetadataSetRowId == false) {
        $.ajax({
          'url': '/filesystem/get_transfer_metadata_set/',
          'type': 'GET',
          'async': false,
          'cache': false,
          'success': function(results) {
             transferMetadataSetRowId = results.id;
          },
          'error': function() {
            alert('Error: contact administrator.');
          }
        });
      }

      var $transferPathRowEl = $('<div></div>')
        , $transferPathEl = $('<span class="transfer_path"></span>')
        , $transferPathDeleteRl = $('<span style="margin-left: 1em;"><img src="/media/images/delete.png" /></span>');

      $transferPathDeleteRl.click(function() {
        $transferPathRowEl.remove();
      });

      $transferPathEl.html(result.path);
      $transferPathRowEl.append($transferPathEl);
      $transferPathRowEl.append($transferPathDeleteRl);
      $('#' + targetCssId).append($transferPathRowEl);
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
