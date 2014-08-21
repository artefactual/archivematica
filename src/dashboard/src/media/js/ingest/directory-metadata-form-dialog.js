var DirectoryMetadataFormView = Backbone.View.extend({

  initialize: function() {
    this.template = _.template(this.options.template);
  },

  show: function(path, postSaveLogic) {
    if (typeof path !== 'undefined')
    {
      var self = this;

      this.path = path;
      this.postSaveLogic = postSaveLogic;

      this.fetchAvailableLevelsOfDescription(
        this.fetchMetadataThenShowModalCallback(),
        this.requestErrorCallback('fetching levels of description')
      );
    }
  },

  fetchAvailableLevelsOfDescription: function(success, error) {
    var self = this;

    // Get available AtoM levels of description
    $.ajax({
      url: '/api/administration/dips/atom/levels/',
      type: 'GET',
      async: false,
      cache: false,
      success: success,
      error: error
    });
  },

  fetchMetadataThenShowModalCallback: function() {
    var self = this;

    return function(levelsOfDescription) {
      var metadataSuccess = function(metadata) {
        self.prepareDataForRendering(metadata, levelsOfDescription);
        self.el.modal({show: true});
        self.render();
      };

      self.fetchMetadata(
        metadataSuccess,
        self.requestErrorCallback('fetching metadata')
      );
    }
  },

  fetchMetadata: function(success, error) {
    $.ajax({
      url: '/api/filesystem/metadata/',
      type: 'GET',
      async: false,
      cache: false,
      data: {
        path: this.path
      },
      success: success,
      error: error
    });
  },

  prepareDataForRendering: function(metadata, levelsOfDescription) {
    // Simplify level data structure for rendering
    var levels = [{id: '', name: '--Select level of description--'}];

    // Add objects representing each level
    for (var index in levelsOfDescription) {
      // Get id, name in object (which should only have one property: the id)
      for (var id in levelsOfDescription[index]) {
        levels.push({
          id: id,
          name: levelsOfDescription[index][id]
        });
      }
    }

    this.availableLevels = levels;
    this.currentLevel = metadata.level_of_description;
  },

  saveLevelOfDescription: function(callback) {
    var self = this;

    // Do POST ajax call to save LOD
    $.ajax({
      url: '/api/filesystem/metadata/',
      type: 'POST',
      async: false,
      cache: false,
      data: {
        path: self.path,
        level_of_description: self.currentLevelId
      },
      success: function(levelsOfDescription) {
        callback(self.currentLevelName);
      },
      error: self.requestErrorCallback('saving metadata')
    });
  },

  requestErrorCallback: function(requestDescription) {
    return function() {
      alert('Error ' + requestDescription + '.');
    };
  },

  render: function() {
    var self = this,
        context;

    context = {
      levels: this.availableLevels,
      currentLevel: this.currentLevel
    };

    // Render dialog
    this.el.html(this.template(context));

    // Activate modal hiding buttons
    $('#directory-metadata-form-close, #directory-metadata-form-cancel')
      .click(function() {
        self.el.modal({show: false});
      });

    // Activate modal save button
    $('#directory-metadata-form-save')
      .click(function() {
        self.saveLevelOfDescription(function() {
          self.el.modal({show: false});
          self.postSaveLogic();
        });
      });

    // Activate level of description selection
    $('#directory-metadata-form-lod-select')
      .change(function() {
        self.currentLevelId = $('#directory-metadata-form-lod-select').val();
        self.currentLevelName = $('#directory-metadata-form-lod-select option:selected').text();
      });

    return this;
  }
});

// Instantiate form when DOM's available
$(document).ready(function() {
  directoryMetadataForm = new DirectoryMetadataFormView({
    el: $('#directory-metadata-form'),
    template: $('#directory-metadata-form-modal').html()
  });
});
