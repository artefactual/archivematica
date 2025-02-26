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
          'DIPUUID',
          'objectPaths',
          'resourceData',
          'initialMatches',
          'objectPaneCSSId',
          'objectPaneSearchCSSId',
          'objectPanePathsCSSId',
          'resourcePaneCSSId',
          'resourcePaneSearchCSSId',
          'resourcePaneItemsCSSId',
          'matchButtonCSSId',
          'matchPaneCSSId',
          'matchPanePairsCSSId',
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

    // path UUIDs will be stored here using data supplied by the objectPaths parameter
    this.pathData = {};

    // set matcher state maintenance properties
    this.resourceCollection = new ATKMatcherCollection();
    this.selectedResourceCSSId = false; // resource currently selected in UI

    this.pairCollection = new ATKMatcherCollection();
  },

  render: function() {
    $(this.el).append(this.matcherLayoutTemplate());

    // render initial data
    this.renderObjectPaths();
    this.populateResourceCollection(this.resourceData);
    this.renderResourceCollection();

    // activate interface behaviour
    this.activateObjectFiltering();
    this.activateResourceSelection();
    this.activateResourceFiltering();
    this.activateResourceSorting();
    this.activateMatchButtonAndKeypressResponse();
    this.activateConfirmButton();
    this.activateCancelButton();
    this.populateMatches();
  },

  populateMatches: function() {
    var self = this;
    // Find the path in self.objectPaths, given the file UUID
    var path;
    self.initialMatches.forEach(function(pair) {
      for (var i in self.objectPaths) {
        if (self.objectPaths[i].uuid == pair.file_uuid) {
          path = self.objectPaths[i].path;
          break;
        }
      }
      var css_id = self.findIDFromPath(path);
      self.matchPair(css_id, path, pair.resource, false);
    })
  },

  findUUIDFromPath: function(path) {
    var self = this;
    var uuid;

    self.objectPaths.forEach(function(object_path) {
      if (object_path['path'] == path) { uuid = object_path['uuid']; }
    });

    return uuid;
  },

  postMatch: function(resource_id, path) {
    var self = this,
      url = window.location.href.split('/').slice(0, 7).join('/') + '/match/';

    var uuid = self.findUUIDFromPath(path);

    $.ajax({
      url: url,
      context: this,
      type: 'POST',
      data: JSON.stringify({
              'resource_id': resource_id,
              'file_uuid': uuid
      }),
      dataType: 'json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function(result) {
        // TODO: make the display of the "delete" button conditional on success
      }
    });
  },

  deleteMatch: function(resource_id, path) {
    var self = this,
      url = window.location.href.split('/').slice(0, 7).join('/') + '/match/';

    var uuid = self.findUUIDFromPath(path);

    $.ajax({
      url: url,
      context: this,
      type: 'DELETE',
      data: JSON.stringify({
              'resource_id': resource_id,
              'file_uuid': uuid,
      }),
      dataType: 'json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function(result) {
        // TODO: delete the pair from the UI, and reactivate the elements?
        //       Or leave that to happen independent of the request?
      }
    })
  },

  // this can be replaced with Underscore's truncation once we update
  // Underscore...
  truncate: function(string, length, truncation) {
      length = length || 30;
      truncation = _.isUndefined(truncation) ? '...' : truncation;
      return string.length > length ?
        string.slice(0, length - truncation.length) + truncation : String(string);
    },

  renderObjectPaths: function() {
    var self = this,
        index = 0;

    // Sort by path
    this.objectPaths.sort(function (a, b){return a.path.toLowerCase().localeCompare(b.path.toLowerCase())})
    // add each path to object pane
    this.objectPaths.forEach(function(pathData) {
      // create object path representation (checkbox and label)
      var newObjectPath = $(self.objectPathTemplate({
        'index': index,
        'path': pathData.path,
        'truncated_path': self.truncate(pathData.path, 40)}
      ));

      self.pathData[pathData.path] = pathData.uuid;

      self.activateCheckboxMultipleSelection(index, newObjectPath);
      $('#' + self.objectPanePathsCSSId).append(newObjectPath);
      index++;
    });
  },

  activateCheckboxMultipleSelection: function(index, newObjectPath) {
    var self = this;

    // add shift-click handling for selecting multiple paths
    newObjectPath.children().click(function(event) {
      // don't respond to label click event, just checkbox
      if ($(this).get(0).tagName == 'INPUT') {
        // only want to perform this logic if the user has checked a checkbox
        if ($(this).attr('checked') == 'checked') {
          // if user has shift-clicked, try multiple select
          if (event.shiftKey && self.pathIndexOfLastChecked != undefined) {
            // try multiple select direction based on the user's last checked path
            if (self.pathIndexOfLastChecked < index) {
              // work backwards, checking previously rendered checkboxes, to try to find
              // one that's checked
              var previousIndex = index - 1;
              while (previousIndex >= 0) {
                // if a checkbox is checked, check all between it and the one that
                // was clicked
                if ($('#path_' + previousIndex + '_checkbox').attr('checked') == 'checked') {
                  for(var checkIndex = previousIndex + 1; checkIndex < index; checkIndex++) {
                    // check checkbox
                    $('#path_' + checkIndex + '_checkbox').attr('checked', 'checked');
                  }

                  break;
                }
                previousIndex--;
              }
            } else {
              // work forwards, checked checkboxes rendered after this checkbox, to find
              // one that's checked
              var nextIndex = index + 1;
              while (nextIndex < self.objectPaths.length) {
                if ($('#path_' + nextIndex + '_checkbox').attr('checked') == 'checked') {
                  for(var checkIndex = nextIndex - 1; checkIndex > index; checkIndex--) {
                    // check checkbox
                    $('#path_' + checkIndex + '_checkbox').attr('checked', 'checked');
                  }

                  break;
                }
                nextIndex++;
              }
            }
          }

          // take note that this was the last checkbox checked
          self.pathIndexOfLastChecked = index;
        }
      }
    });
  },

  populateResourceCollection: function(resourceData, level) {
    level = level || 0;

    var padding = '';

    for (var index = 0; index < level; index++) {
      padding = padding + '&nbsp;&nbsp;';
    }

    // store internal representation for reference
    resourceData['padding'] = padding;

    resourceData['resourceId'] = resourceData.id;
    this.resourceCollection.add(resourceData);

    // recurse if children are found
    if (resourceData.children) {
      var self = this;

      resourceData.children.forEach(function(child) {
        self.populateResourceCollection(child, level + 1);
      });
    }
  },

  renderResourceCollection: function() {
    var self = this;

    // empty resource pane
    $('#' + self.resourcePaneItemsCSSId).empty();

    // add items in collection to pane
    this.resourceCollection.models.forEach(function (resource) {

      // padding only makes sense when sorted by the order in which the
      // data was origianlly provided by the server (ordered by
      // level of description, then title)
      if (
        self.resourceCollection.sortAttribute == undefined
        || self.resourceCollection.sortAttribute == 'sortPosition'
      ) {
        padding = resource.get('padding');
      } else {
        padding = '';
      }

      // render individual resource
      $('#' + self.resourcePaneItemsCSSId).append(
        self.resourceItemTemplate({
          'tempId':             resource.id,
          'padding':            padding,
          'title':              resource.get('title'),
          'truncated_title':    self.truncate(resource.get('title'), 40),
          'levelOfDescription': resource.get('levelOfDescription'),
          'identifier':         resource.get('identifier'),
          'dates':              resource.get('dates')
        })
      );

      // highlight if it has been paired with any objects
      if (resource.get('used')) {
        $('#resource_' + resource.id + ' > td').addClass('atk-matcher-resource-item-paired');
      }
    });
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

  activateResourceSorting: function() {
    var self = this;

    // add comparator
    this.resourceCollection.comparator = function(resource) {
      if (self.resourceCollection.sortAttribute != undefined) {
        return resource.get(self.resourceCollection.sortAttribute).toLowerCase();
      } else {
        return resource.id;
      }
    };

    // activate sort handles
    this.resourceCollection.sortAttribute = 'sortPosition';
    $('.atk_resource_sort').each(function() {
      var sortHandleCSSId = $(this).attr('id'),
          resourceAttribute = sortHandleCSSId.replace('sort_by_', '');

      $(this).click(function() {
        // establish sort direction
        if (self.resourceCollection.lastSortedBy != resourceAttribute) {
          self.resourceCollection.sortDirection = 'asc';
        } else {
          if (self.resourceCollection.sortDirection == 'asc') {
            self.resourceCollection.sortDirection = 'desc'
          } else {
            self.resourceCollection.sortDirection = 'asc'
          }
        }
        self.resourceCollection.lastSortedBy = resourceAttribute;

        // perform sort
        self.resourceCollection.sortAttribute = resourceAttribute;
        self.resourceCollection.sort();

        // reverse sort if applicable
        if (self.resourceCollection.sortDirection == 'desc') {
          self.resourceCollection.models.reverse();
        }

        // render resource collection and re-activate resource selection
        self.renderResourceCollection();
        self.activateResourceSelection();
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

  buildResourceObject: function(resource_id) {
    var self = this;
    var resource = self.findResourceFromCSSId(resource_id);
    return {
      'cssId': resource.attributes.id,
      'dates': resource.get('dates'),
      'id': resource.get('id'),
      'identifier': resource.get('identifier'),
      'levelOfDescription': resource.get('levelOfDescription'),
      'model': resource,
      'resourceId': resource.get('resourceId'),
      'sortPosition': resource.get('sortPosition'),
      'title': resource.get('title'),
    }
  },

  matchPair: function(id, path, resource, post_data) {
    var self = this;
    $('#' + id + ' > input').attr('disabled', 'disabled');
    $('#' + id + ' > label').addClass('atk-matcher-disabled-object-label');

    if (undefined !== resource.model) {
      // take note that resource has had objects assigned to it and visually
      // indicate it
      resource.model.set({'used': true});
      $('#resource_' + resource.model.id + ' > td').addClass('atk-matcher-resource-item-paired');
    }

    // store pair in collection for easy retrieval
    self.pairCollection.add({
      'DIPUUID':                    self.DIPUUID,
      'objectPath':                 path,
      'objectUUID':                 self.pathData[path],
      'resourceId':                 resource.id,
      'resourceCSSId':              resource.cssId,
      'resourceLevelOfDescription': resource.levelOfDescription,
      'resourceSortPosition':       resource.sortPosition
    });

    // get the pair model that was added
    var pairModel = self.pairCollection.lastModelAdded();

    var $newMatchEl = $(self.matchItemTemplate({
      'tempId': pairModel.id,
      'path': path,
      'truncated_path': self.truncate(path, 40),
      'title': resource.title,
      'truncated_title': self.truncate(resource.title, 40),
      'identifier': resource.identifier,
      'levelOfDescription': resource.levelOfDescription,
      'dates': resource.dates
    }));

    // POST the new match to the server
    if (post_data) { self.postMatch(resource.resourceId, path); }

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

    // hack to fix Firefox issue
    $('tr').css('display', 'table-row');

    // fade added element in
    $newMatchEl.fadeIn('slow');

    // enable deletion of match
    (function(index, pathId, resourceId) {
      $('#match_delete_' + index).click(function() {
        // send delete request to the server
        var pair = self.pairCollection.get(index);
        self.deleteMatch(pair.attributes.resourceId, pair.attributes.objectPath);

        // enable checkbox and remove greying out of associated label
        $('#' + pathId + ' > input').removeAttr('disabled');
        $('#' + id + ' > label').removeClass('atk-matcher-disabled-object-label');

        // un-check checkbox
        $('#' + id + ' > input').removeAttr('checked');

        // remove visual and internal pair representations
        $('#match_' + index).remove();
        self.pairCollection.remove(pair);

        // see if the resource in the pairing is still associated with any objects
        var found = self.pairCollection.find(function(item) {
          return item.get('resourceCSSId') === pair.get('resourceCSSId');
        });

        // if the resource isn't associated with any objects, remove usage highlighting
        if (found == undefined) {
          // TODO: redo using a class
          $('#' + pair.get('resourceCSSId') + ' > td').removeClass('atk-matcher-resource-item-paired');
          // set used in resource with ID resourceId to false
          var resource = self.resourceCollection.get({id: resourceId});
          resource.set({used: false});
        }
      });
    })(pairModel.id, id, resource.id)
    self.matchIndex++;
  },

  findIDFromPath: function(path) {
    var self = this;
    var id = self.objectPanePathsCSSId;
    return $('#' + id + '> div > label[title="' + path + '"]').parent().attr('id');
  },

  findResourceFromCSSId: function(resource_id) {
    var self = this;
    for (var i in self.resourceCollection.models) {
      var m = self.resourceCollection.models[i];
      if ("resource_" + m.id == resource_id) {
        return m;
      }
    }
  },

  activateMatchButtonAndKeypressResponse: function() {
    var self = this;

    var doMatch = function() {
      // Stop if no resources have been selected.
      if (!self.selectedResourceCSSId) {
        self.notify(gettext('No resource selected.'));
        return;
      }

      // Stop if no objects have been selected.
      var selectedPaths = self.getSelectedPaths();
      if (!selectedPaths.length) {
        self.notify(gettext('No objects selected.'));
        return;
      }

      // Pair
      selectedPaths.forEach(function(item) {
        var resource = self.buildResourceObject(self.selectedResourceCSSId);
        self.matchPair(item.id, item.path, resource, true);
      });

      // Deselect resource
      self.selectedResourceCSSId = false;
      self.resetBackgroundOfResourceTableRows();
    };

    $(document).bind('keypress', function(e) {
       if (e.which === 13) {
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

  sendPairData: function(url, success, error) {
    var self = this;

    $.ajax({
      context: this,
      type: 'POST',
      dataType: 'json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      data: {pairs: self.pairCollection.toJSON()},
      success: function(result)
        {
          success(result);
        },
      error: function()
        {
          error();
        },
      url: url
    });
  },

  activateConfirmButton: function() {
    $('#' + this.confirmButtonCSSId).click(function() {
      window.location.href = '/ingest';
    });
  },

  activateCancelButton: function() {
    var self = this,
        fadeInElementCSSIds = [
          this.objectPaneCSSId,
          this.resourcePaneCSSId
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


  /**
   * Return an array of objects with details of the objects that have been
   * selected.
   */
  getSelectedPaths: function() {
    return $('#' + this.objectPanePathsCSSId + ' > div').map(function() {
      var $this = $(this);
      var $input = $this.children('input');

      if ($input.is(':disabled') || !$input.is(':checked')) {
        return undefined;
      }

      return {
        'id': $this.attr('id'),
        'path': $this.children('label').attr('title')
      };
    }).get();
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
      title: gettext('Warning'),
      width: 640,
      height: 200,
      buttons: [{
        text: gettext('Dismiss'),
        click: function() { $(this).dialog('close'); }
      }]
    });
  }
});
