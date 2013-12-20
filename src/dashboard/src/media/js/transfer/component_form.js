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

var active_component;
var components = {};

function createMetadataSetID() {
  var set_id;

  $.ajax({
    'url': '/transfer/create_metadata_set_uuid/',
    'type': 'GET',
    'async': false,
    'cache': false,
    'success': function(results) {
       set_id = results.uuid;
    },
    'error': function() {
      alert('Error: contact administrator.');
    }
  });

  return {uuid: set_id};
}

// Removes all form values associated with the given UUID,
// along with the metadata row set in the database
function removeMetadataForms(uuid) {
  $.ajax({
    'url': '/transfer/cleanup_metadata_set/' + uuid + '/',
    'type': 'POST',
    'async': false,
    'cache': false,
    'error': function() {
      alert('Failed to clean up metadata for UUID: ' + component.uuid);
    }
  });
}

var TransferComponentFormView = Backbone.View.extend({
  initialize: function(options) {
    this.form_layout_template = _.template(options.form_layout_template);
    this.modal_template = options.modal_template;
    this.sourceDirectories = options.sourceDirectories;
  },

  showSelector: function(sourceDir) {
    // display action selector in modal window
    $(this.modal_template).modal({show: true});

    // make it destroy rather than hide modal
    $('#transfer-component-select-close, #transfer-component-select-cancel')
      .click(function() {
        $('#transfer-component-select-modal').remove();
      });

    // add directory selector
    var locationUUID = $('#path_source_select').children(':selected').val();
    createDirectoryPicker(
      locationUUID,
      sourceDir,
      'transfer-component-select-modal',
      'path_container'
    );
  },

  addedPaths: function() {
    var paths = [];
    component_keys = Object.keys(components);
    for (var i in component_keys) {
      key = component_keys[i];
      paths.push(components[key]);
    }
    return paths;
  },

  startTransfer: function(transfer) {
    var path;

    // Clean up unused metadata forms that may have been entered but
    // not associated with any files
    // active_component is set if a metadata row has been started, but
    // not yet been associated with a component via the browse button.
    if (active_component) {
      removeMetadataForms(active_component.uuid);
    }
    // re-enable transfer type select
    $('#transfer-type').removeAttr('disabled');
    $('#transfer_metadata_edit_button').hide('fade', {}, 250);
    // transfer directory counter goes back to 1 for the next transfer
    transferDirectoryPickerPathCounter = 1;

    $('.transfer-component-activity-indicator').show();
    // get path to temp directory in which to copy individual transfer
    // components
    $.ajax({
      url: '/filesystem/get_temp_directory/',
      type: 'GET',
      cache: false,
      success: function(results) {
        if (results['error']) {
          alert(results['error']);
          $('.transfer-component-activity-indicator').hide();
          return;
        }

        var tempDir = results.tempDir;
        var error = false;
        // copy each transfer component to the temp directory
        console.log(transfer.sourcePaths);
        for (var index in transfer.sourcePaths) {
          var component = transfer.sourcePaths[index];
          var path = component.path;
          var uuid = component.uuid;

          $.ajax({
            url: '/filesystem/copy_transfer_component/',
            type: 'POST',
            async: false,
            cache: false,
            data: {
              name:        transfer.name,
              path:        path,
              destination: tempDir
            },
            success: function(results) {
              if (results['error']) {
                alert(results.message);
                error = true;
              }
            }
          });

        if (error) {
          $('.transfer-component-activity-indicator').hide();
          return;
        }

          // move from temp directory to appropriate watchdir
          var url = '/filesystem/ransfer/'
            , isArchiveFile = path.toLowerCase().indexOf('.zip') != -1 || path.toLowerCase().indexOf('.tgz') != -1 || path.toLowerCase().indexOf('.tar.gz') != -1
            , filepath;

          // if transfer is a ZIP file, then extract basename add to temporary directory
          if (isArchiveFile) {
            filepath = tempDir + '/' + path.replace(/\\/g,'/').replace( /.*\//, '' );
          } else {
            filepath = tempDir + '/' + transfer.name;
          }

          $.ajax({
            url: url,
            type: 'POST',
            async: false,
            cache: false,
            data: {
              filepath:  filepath,
              type:      transfer.type,
              accession: transfer.accessionNumber,
              transferMetadataSetRowUUID: uuid
            },
            success: function(results) {
              if (results['error']) {
                alert(results.message);
              }

              $('#transfer-name').val('');
              $('#transfer-accession-number').val('');
              $('#transfer-name-container').show();
              $('#transfer-type').val('standard');
              $('#path_container').html('');
              $('.transfer-component-activity-indicator').hide();
            }
          });
        }
      }
    });

    components = {};
  },

  render: function() {
    var $pathAreaEl = $('<div></div>')
       , $pathContainerEl = $('<div id="path_container"></div>');

    this.pathContainerEl = $pathContainerEl;

    // add button to add paths via a pop-up selector
    var $buttonContainer = $('<div></div>')
      , $addButton = $('<span id="path_add_button" class="btn">Browse</span>')
      , $sourceDirSelect = $('<select id="path_source_select"></select>')
      , $startTransferButton = $('<span id="start_transfer_button" class="btn success">Start transfer</span>')
      , $metadataEditButton = $('<span id="transfer_metadata_edit_button" class="btn metadata-edit">Add metadata</span>')
      , self = this;

    $buttonContainer
      .append($sourceDirSelect)
      .append($addButton)
      .append($startTransferButton)
      .append($metadataEditButton);

    $pathAreaEl.append($buttonContainer);

    // add path container to parent container
    $pathAreaEl.append($pathContainerEl);

    // populate select with source directory values
    $.each(this.sourceDirectories, function(id, path) {   
      $sourceDirSelect
        .append($("<option></option>")
        .attr("value", id)
        .text(path)); 
    });

    // populate view's DOM element with template output
    var context = {
      transfer_paths: $pathAreaEl.html()
    };
    $(this.el).html(this.form_layout_template(context));

    // make add button clickable
    $('#path_add_button').click(function() {
      // add modal containing directory selector
      // selecting makes modal disappear, adds directory, and re-renders
      self.showSelector($('#path_source_select').children(':selected').text());
    });

    // add logic to determine whether or not transfer name needs to be
    // visible if transfer type changed
    $('#transfer-type').change(function() {
      if ($(this).val() == 'zipped bag') {
        $('#transfer-name-container').hide('slide', {direction: 'left'}, 250);
      } else if($(this).is(':hidden')) {
        $('#transfer-name-container').show('slide', {direction: 'left'}, 250);
      }

      // If the transfer type is a Disk Image, the metadata edit button is visible;
      // otherwise, we hide it
      if ($(this).val() == 'disk image') {
        $('#transfer_metadata_edit_button').show('fade', {}, 250);
      } else {
        $('#transfer_metadata_edit_button').hide('fade', {}, 250);
      }
    });

    // The metadata set edit button is available as soon as a disk image transfer type is selected.
    // This allows for entering metadata before the associated transfer component is created,
    // for instance to write metadata about a disk image before the image file is ready to be added
    // as a new transfer component.
    // It creates a metadata form associated with a placeholder path; that path will be updated to
    // point at the actual component path once a new transfer path is added.
    $('#transfer_metadata_edit_button').click(function() {
      if (!active_component) { active_component = createMetadataSetID(); }
      metadata_url = '/transfer/component/' + active_component.uuid;
      window.open(metadata_url, '_blank');
    });

    // make start transfer button clickable
    $('#start_transfer_button').click(function() {
      var transferName = $('#transfer-name').val();

      // if transfering a zipped bag, give it a dummy name
      if ($('#transfer-type').val() == 'zipped bag') {
        transferName = 'ZippedBag';
      }

      if (!transferName)
      {
        alert('Please enter a transfer name');
      } else {
        var paths = self.addedPaths();
        if (!paths.length) {
          alert('Please click "Browse" to add one or more paths from the source directory.');
        } else {
          var transferData = {
            'name':            transferName,
            'type':            $('#transfer-type').val(),
            'accessionNumber': $('#transfer-accession-number').val(),
            'sourcePaths':     paths
          };
          self.startTransfer(transferData);
        }
      }
    });
  }
});
