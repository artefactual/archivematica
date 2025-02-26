/*
Modification of transfer/component_form.js to display and allow selection of files.
*/

var active_component;
var components = {};

var MetadataFormView = Backbone.View.extend({
  initialize: function(options) {
    this.form_layout_template = _.template(options.form_layout_template);
    this.modal_template = options.modal_template;
    this.sourceDirectories = options.sourceDirectories;
    this.sipUUID = options.sipUUID;
  },

  showSelector: function(sourceDir) {
    // display file browser
    $('.inline-file-explorer').show();

    // hide file browser on close button click
    $('.inline-file-explorer button.close').on('click', function () {
      $('.inline-file-explorer').hide();
    });

    // add directory selector
    var locationUUID = $('#path_source_select').children(':selected').val();
    createDirectoryPicker(
      locationUUID,
      sourceDir,
      'path_container',
      'add-metadata-files-path-item',
      function(entry) {  // Display everything
        return true;
      }
    );
  },

  // This function is solely used for paths to be POSTed to the server,
  // so all paths must be base64-encoded to guard against
  // potential non-unicode characters
  addedPaths: function() {
    var paths = [];
    $('.transfer_path').each(function() {
      // paths.push($(this).prop("id"));
      paths.push(Base64.encode($(this).prop("id")));
    });
    return paths;
  },

  addFiles: function(sourcePaths) {
    $('.activity-indicator').show()
    // get path to temp directory in which to copy individual transfer
    // components
    $.ajax({
      url: '/filesystem/copy_metadata_files/',
      type: 'POST',
      cache: false,
      data: {
        sip_uuid: this.sipUUID,
        source_paths: sourcePaths,
      },
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function(results) {
        if (results['error']) {
          alert(results['error'])
          $('.activity-indicator').hide()
          return;
        }
        $('#path_container').html('')
        $('.activity-indicator').hide()

      }
    })
  },

  render: function() {
    var $pathAreaEl = $('<div></div>')
    , $pathContainerEl = $('<div id="path_container"></div>');

    this.pathContainerEl = $pathContainerEl;

    // add button to add paths via a pop-up selector
    var $buttonContainer = $('<div></div>')
    , $addButton = $('<span id="path_add_button" class="btn btn-default">' + gettext('Browse') + '</span>')
    , $sourceDirSelect = $('<select id="path_source_select" class="form-control"></select>')
    , $addFilesButton = $('<span id="start_transfer_button" class="btn btn-success">' + gettext('Add files') + '</span>')
    , self = this;

    $buttonContainer
    .append($sourceDirSelect)
    .append($addButton)
    .append($addFilesButton);

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

    // make start transfer button clickable
    $('#start_transfer_button').click(function() {
      var sourcePaths = self.addedPaths()
      // Must have at least one metadata path
      if (!sourcePaths.length) {
        alert(gettext('Please select at least one metadata file.'))
      } else {
        self.addFiles(sourcePaths)
      }
    });
  }
});
