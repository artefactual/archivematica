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
  },

  lastModelAdded: function() {
    return this.at(this.length - 1);
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
          'matchPanePairsCSSId',
          'buttonPaneCSSId',
          'saveButtonCSSId',
          'confirmButtonCSSId',
          'cancelButtonCSSId'
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
    this.selectedResourceCSSId = false; // resource currently selected in UI

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
    this.activateMatchButtonAndKeypressResponse();
    this.activateSaveButton();
    this.activateConfirmButton();
    this.activateCancelButton();
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

    var resourceModel = this.resourceCollection.lastModelAdded();

    // display resource
    $('#' + this.resourcePaneItemsCSSId).append(
      this.resourceItemTemplate({
        'tempId':             resourceModel.id,
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
      var filterTerm = $(this).val().toLowerCase();

      // cycle through each object path, hiding or showing based on the filter term
      $('#' + self.objectPanePathsCSSId)
        .children()
        .each(function() {
          if ($(this).children('label').text().toLowerCase().indexOf(filterTerm) == -1) {
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
      var newSelectionCSSId = $(this).attr('id');

      // reset background of resource table rows
      self.resetBackgroundOfResourceTableRows();

      // if a new selection, highlight clicked row and set current selection to its CSS ID
      if (self.selectedResourceCSSId != newSelectionCSSId) {
        $(this).css('background-color', '#ffcc00');
        self.selectedResourceCSSId = newSelectionCSSId;
      } else {
        // ...otherwise, set to no selection
        self.selectedResourceCSSId = false;
      }
    });
  },

  resetBackgroundOfResourceTableRows: function() {
    $('#' + this.resourcePaneItemsCSSId + ' > tr').css('background-color', '');
  },

  activateResourceFiltering: function() {
    var self = this;

    $('#' + this.resourcePaneSearchCSSId + ' > input').keyup(function() {
      var filterTerm = $(this).val().toLowerCase();

      // cycle through each item, hiding or showing based on the filter term
      $('#' + self.resourcePaneItemsCSSId)
        .children()
        .each(function() {
          if ($(this).text().toLowerCase().indexOf(filterTerm) == -1) {
            $(this).hide();
          } else {
            $(this).show();
          }
        });
    });
  },

  activateMatchButtonAndKeypressResponse: function() {
    var self = this;

    var doMatch = function() {
      // if a resource is highlighted, attempt to add selected paths
      if (self.selectedResourceCSSId) {
        var selectedPaths = self.getSelectedPaths();

        // if any paths have been selected
        if(selectedPaths.length) {
          selectedPaths.forEach(function(item) {
            // disable the checkbox on the path being matched
            $('#' + item.id + ' > input').attr('disabled', 'disabled');
            $('#' + item.id + ' > label').addClass('atk-matcher-disabled-object-label');

            var resource = self.resourceCollection.get(
              self.indexNumberFromCSSId(self.selectedResourceCSSId)
            );

            // store pair in collection for easy retrieval
            self.pairCollection.add({
              'objectPath':    item.path,
              'resourceIdentifier': resource.get('identifier'),
              'resourceSortPosition': resource.get('sortPosition')
            });

            // get the pair model that was added
            var pairModel = self.pairCollection.lastModelAdded();

            var $newMatchEl = $(self.matchItemTemplate({
              'tempId': pairModel.id,
              'path': item.path,
              'title': resource.get('title'),
              'identifier': resource.get('identifier'),
              'levelOfDescription': resource.get('levelOfDescription'),
              'dates': resource.get('dates')
            }));

            // hide new pair, add it to the pane, then fade it in
            $newMatchEl.hide();

            // logic to place it according to sort position
            var pairPlaced = false;
            $('#' + self.matchPanePairsCSSId).children().each(function() {
              var pairCSSId = $(this).attr('id'),
                  pairId = self.indexNumberFromCSSId(pairCSSId),
                  pairPosition = self.pairCollection.get(pairId).get('resourceSortPosition');

              if (pairPosition > pairModel.get('resourceSortPosition')) {
                $('#' + pairCSSId).parent().prepend($newMatchEl);
                pairPlaced = true;
              }
            });

            // if the pair hasn't been placed, add it to the end
            if (!pairPlaced) {
              $('#' + self.matchPanePairsCSSId).append($newMatchEl);
            }

            // fade added element in and show Save button
            $newMatchEl.fadeIn('slow');
            $('#' + self.saveButtonCSSId).show();

            // enable deletion of match
            (function(index, pathId) {
              $('#match_delete_' + index).click(function() {
                // enable checkbox and remove greying out of associated label
                $('#' + pathId + ' > input').removeAttr('disabled');
                $('#' + item.id + ' > label').removeClass('atk-matcher-disabled-object-label');

                // un-check checkbox
                $('#' + item.id + ' > input').removeAttr('checked');

                // remove visual and internal pair representations
                $('#match_' + index).remove();
                self.pairCollection.remove(self.pairCollection.get(index));

                // hide save button if no pairs now exist
                if (self.pairCollection.length == 0) {
                  $('#' + self.saveButtonCSSId).hide();
                }
              });
            })(pairModel.id, item.id)
            self.matchIndex++;
          });

          // deselect resource
          self.selectedResourceCSSId = false;
          self.resetBackgroundOfResourceTableRows();
        } else {
          self.notify('No objects selected.');
        }
      } else {
        self.notify('No resource selected.');
      }
    };

    $(document).bind('keypress', function(e){
       if(e.which === 13) {
         doMatch();
       }
    });

    $('#' + this.matchButtonCSSId).click(doMatch);
  },

  fadeElementsByCSSIds: function(ids, type, speed) {
    ids.forEach(function(id) {
      if (type == 'in') {
        $('#' + id).fadeIn(speed);
      } else {
        $('#' + id).fadeOut(speed);
      }
    });
  },

  activateSaveButton: function() {
    var self = this,
        fadeOutElementCSSIds = [
          this.objectPaneCSSId,
          this.resourcePaneCSSId,
          this.buttonPaneCSSId,
          this.saveButtonCSSId
        ],
        fadeInElementCSSIds = [
          this.confirmButtonCSSId,
          this.cancelButtonCSSId
        ];

    $('#' + self.saveButtonCSSId).click(function () {
      self.fadeElementsByCSSIds(fadeOutElementCSSIds, 'out', 'fast');
      self.fadeElementsByCSSIds(fadeInElementCSSIds, 'in', 'fast');
    });
  },

  activateConfirmButton: function() {
    var self = this;
    $('#' + self.confirmButtonCSSId).click(function() {
      console.log(self.pairCollection.toJSON());
    });
  },

  activateCancelButton: function() {
    var self = this,
        fadeInElementCSSIds = [
          this.objectPaneCSSId,
          this.resourcePaneCSSId,
          this.buttonPaneCSSId,
          this.saveButtonCSSId
        ],
        fadeOutElementCSSIds = [
          this.confirmButtonCSSId,
          this.cancelButtonCSSId
        ];

    $('#' + self.cancelButtonCSSId).click(function() {
      self.fadeElementsByCSSIds(fadeInElementCSSIds, 'in', 'fast');
      self.fadeElementsByCSSIds(fadeOutElementCSSIds, 'out', 'fast');
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
