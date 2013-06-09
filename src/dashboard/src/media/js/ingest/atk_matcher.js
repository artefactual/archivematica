// manages auto-incrementing of internal ID
var ATKMatcherCollection = Backbone.Collection.extend({
  initialize: function() {
    this.currentId = 0;

    var self = this;
    this.bind('add', function(model, collection) {
      self.currentId++;
      model.id = self.currentId;
      self._byId[model.id] = model;
    });
  }
});

var ATKMatcherView = Backbone.View.extend({
  initialize: function(options) {
    var self = this,
        manditoryProperties = [
          'objectPaths',
          'resourceData',
          'objectPaneCSSId',
          'objectPaneSearchCSSId',
          'objectPanePathsCSSId',
          'resourcePaneCSSId',
          'resourcePaneSearchCSSId',
          'resourcePaneItemsCSSId',
          'matchButtonCSSId',
          'matchPaneCSSId',
          'matchPanePairsCSSId'
        ];

    // set mandatory properties
    manditoryProperties.forEach(function(property) {
      self[property] = options[property] || alert(property + ' required.');
    });

    // set up matcher template methods
    this.matcherLayoutTemplate  = _.template(options.matcherLayoutTemplate);
    this.objectPathTemplate     = _.template(options.objectPathTemplate);
    this.resourceItemTemplate   = _.template(options.resourceItemTemplate);
    this.matchItemTemplate      = _.template(options.matchItemTemplate);

    // set matcher state maintenance properties
    this.resourceCollection = new ATKMatcherCollection();
    this.selectedResourceId = false; // resource currently selected in UI

    this.pairCollection = new ATKMatcherCollection();
  },

  render: function() {
    $(this.el).append(this.matcherLayoutTemplate());

    // render initial data
    this.renderObjectPaths();
    this.renderResourceData(this.resourceData);

    // activate interface behaviour
    this.activateObjectFiltering();
    this.activateResourceSelection();
    this.activateResourceFiltering();
    this.activateMatchButton();
  },

  renderObjectPaths: function() {
    var self = this,
        index = 0;

    // add each path to object pane
    this.objectPaths.forEach(function(path) {
      $('#' + self.objectPanePathsCSSId).append(
        self.objectPathTemplate({'index': index, 'path': path})
      );
      index++;
    });
  },

  renderResourceData: function(resourceData, level) {
    level = level || 0;

    var padding = '';

    for (var index = 0; index < level; index++) {
      padding = padding + '&nbsp;&nbsp;';
    }

    // store internal representation for reference
    this.resourceCollection.add(resourceData);

    var resourceModel = this.resourceCollection.at(this.resourceCollection.length - 1);

    // display resource
    $('#' + this.resourcePaneItemsCSSId).append(
      this.resourceItemTemplate({
        'index':              resourceModel.id,
        'padding':            padding,
        'title':              resourceData.title,
        'levelOfDescription': resourceData.levelOfDescription,
        'identifier':         resourceData.identifier,
        'dates':              resourceData.dates
      })
    );

    // recurse if children are found
    if (resourceData.children) {
      var self = this;

      resourceData.children.forEach(function(child) {
        self.renderResourceData(child, level + 1);
      });
    }
  },

  activateObjectFiltering: function() {
    var self = this;
    $('#' + this.objectPaneSearchCSSId + ' > input').keyup(function() {
      var filterTerm = $(this).val();

      // cycle through each object path, hiding or showing based on the filter term
      $('#' + self.objectPanePathsCSSId)
        .children()
        .each(function() {
          if ($(this).children('label').text().indexOf(filterTerm) == -1) {
            $(this).hide();
          } else {
            $(this).show();
          }
        });
    });
  },

  activateResourceSelection: function() {
    var self = this;

    $('#' + this.resourcePaneItemsCSSId + ' > tr').click(function() {
      $('#' + self.resourcePaneItemsCSSId + ' > tr').css('background-color', '');
      $(this).css('background-color', '#ffcc00');
      self.selectedResourceId = $(this).attr('id');
    });
  },

  activateResourceFiltering: function() {
    var self = this;

    $('#' + this.resourcePaneSearchCSSId + ' > input').keyup(function() {
      var filterTerm = $(this).val();

      // cycle through each item, hiding or showing based on the filter term
      $('#' + self.resourcePaneItemsCSSId)
        .children()
        .each(function() {
          if ($(this).text().indexOf(filterTerm) == -1) {
            $(this).hide();
          } else {
            $(this).show();
          }
        });
    });
  },

  activateMatchButton: function() {
    var self = this;

    $('#' + this.matchButtonCSSId).click(function() {
      // if a resource is highlighted, attempt to add selected paths
      if (self.selectedResourceId) {
        var selectedPaths = self.getSelectedPaths();

        // if any paths have been selected
        if(selectedPaths.length) {
          selectedPaths.forEach(function(item) {
            // disable the checkbox on the path being matched
            $('#' + item.id + ' > input').attr('disabled', 'disabled');

            var resource = self.resourceCollection.get(self.indexNumberFromCSSId(self.selectedResourceId));

            // store pair in collection for easy retrieval
            self.pairCollection.add({
              'objectPath':    item.path,
              'resourceIdentifier': resource.get('identifier'),
            });

            var pairModel = self.pairCollection.at(self.pairCollection.length - 1);

            var $newMatchEl = $(self.matchItemTemplate({
              'index': pairModel.id,
              'path': item.path,
              'title': resource.get('title'),
              'identifier': resource.get('identifier'),
              'levelOfDescription': resource.get('levelOfDescription'),
              'dates': resource.get('dates')
            }));

            // hide new pair, add it to the pane, then fade it in
            $newMatchEl.hide();
            $('#' + self.matchPanePairsCSSId).append($newMatchEl);
            $newMatchEl.fadeIn('fast');

            (function(index, pathId) {
              $('#match_delete_' + index).click(function() {
                $('#' + pathId + ' > input').removeAttr('disabled');
                $('#match_' + index).remove();
                self.pairCollection.remove(self.pairCollection.get(index));
              });
            })(pairModel.id, item.id)
            self.matchIndex++;
          });
        } else {
          self.notify('No objects selected.');
        }
      } else {
        self.notify('No resource selected.');
      }
    });
  },

  getSelectedPaths: function() {
    var self = this,
        selectedPaths = [];

    $('#' + self.objectPanePathsCSSId + ' > div').each(function() {
      if (
        $(this).children('input').attr('checked') == 'checked'
        && $(this).children('input').attr('disabled') != 'disabled'
      ) {
        selectedPaths.push({
          'id': $(this).attr('id'),
          'path': $(this).children('label').text()
        });
      }
    });

    return selectedPaths;
  },

  indexNumberFromCSSId: function(CSSId) {
    return parseInt(CSSId.substring(
      CSSId.indexOf('_') + 1
    ));
  },

  notify: function(text) {
    var dialog = $('<div>' + text + '</div>');

    setTimeout(function() {
      $(dialog).dialog('close');
    }, 2000);

    dialog.dialog({
      title: 'Warning',
      width: 640,
      height: 200,
      buttons: [{
        text: 'Dismiss',
        click: function() { $(this).dialog('close'); }
      }]
    });
  }
});
