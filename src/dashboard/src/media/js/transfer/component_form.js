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

  // This function is solely used for paths to be POSTed to the server,
  // so all paths must be base64-encoded to guard against
  // potential non-unicode characters
  addedPaths: function() {
    var paths = [];
    $('.transfer_path').each(function() {
      paths.push(Base64.encode($(this).text()));
    });
    return paths;
  },

  startTransfer: function(transfer) {
    $('.transfer-component-activity-indicator').show();
    $.ajax({
      url: '/filesystem/ransfer/',
      type: 'POST',
      cache: false,
      async: false,
      data: {
        name:      transfer.name,
        type:      transfer.type,
        accession: transfer.accessionNumber,
        "paths[]": transfer.sourcePaths
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
      , self = this;

    $buttonContainer
      .append($sourceDirSelect)
      .append($addButton)
      .append($startTransferButton);

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
      } else {
        $('#transfer-name-container').show('slide', {direction: 'left'}, 250);
      }
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
        if (!self.addedPaths().length) {
          alert('Please click "Browse" to add one or more paths from the source directory.');
        } else {
          var transferData = {
            'name':            transferName,
            'type':            $('#transfer-type').val(),
            'accessionNumber': $('#transfer-accession-number').val(),
            'sourcePaths':     self.addedPaths()
          };
          self.startTransfer(transferData);
        }
      }
    });
  }
});
