var ATKMatcherView = Backbone.View.extend({
  initialize: function(options) {
    // data needed for matching
    this.objectPaths     = options.objectPaths || alert('objectPaths required.');
    this.resourceData    = options.resourceData || alert('resourceData required.');

    // CSS ID mapping
    this.objectPaneCSSId        = options.objectPaneCSSId || alert('objectPaneCSSId required.');
    this.objectPaneSearchCSSId  = options.objectPaneSearchCSSId || alert('objectPaneSearchCSSId required.');
    this.objectPanePathsCSSId   = options.objectPanePathsCSSId || alert('objectPanePathsCSSId required.');
    this.resourcePaneCSSId      = options.resourcePaneCSSId || alert('resourcePaneCSSId required.');
    this.resourcePaneItemsCSSId = options.resourcePaneItemsCSSId || alert('resourcePaneItemsCSSId required.');
    this.matchButtonCSSId       = options.matchButtonCSSId || alert('matchButtonCSSId required.');
    this.matchPaneCSSId         = options.matchPaneCSSId || alert('matchPaneCSSId required.');

    // set up matcher template methods
    this.matcherLayoutTemplate  = _.template(options.matcherLayoutTemplate);
    this.objectPathTemplate     = _.template(options.objectPathTemplate);
    this.resourceItemTemplate   = _.template(options.resourceItemTemplate);
    this.matchItemTemplate      = _.template(options.matchItemTemplate);

    // set matcher state maintenance properties
    this.resourceIndex      = 0;
    this.selectedResourceId = false;
    this.matchIndex         = 0;
  },

  render: function() {
    $(this.el).append(this.matcherLayoutTemplate());

    // render initial data
    this.renderObjectPaths();
    this.renderResourceData(this.resourceData);

    // activate interface behaviour
    this.activateObjectFiltering();
    this.activateResourceSelection();
    this.activateMatchButton();
  },

  renderObjectPaths: function() {
    var self = this,
        index = 0;

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

    $('#' + this.resourcePaneItemsCSSId).append(
      this.resourceItemTemplate({
        'index':   this.resourceIndex,
        'padding': padding,
        'title':   resourceData.title
      })
    );

    this.resourceIndex++;

    var self = this;

    if (resourceData.children) {
      resourceData.children.forEach(function(child) {
        self.renderResourceData(child, level + 1);
      });
    }
  },

  activateObjectFiltering: function() {
    var self = this;
    $('#' + this.objectPaneSearchCSSId + ' > input').change(function() {
      var filterTerm = $(this).val();
      $('#' + self.objectPanePathsCSSId)
        .children()
        .each(function() {
          if ($($(this).children('label')[0]).text().indexOf(filterTerm) == -1) {
            $(this).hide();
          } else {
            $(this).show();
          }
        });
    });
  },

  activateResourceSelection: function() {
    var self = this;

    $('#' + this.resourcePaneItemsCSSId + ' > div').click(function() {
      $('#' + self.resourcePaneItemsCSSId + ' > div').css('background-color', '');
      $(this).css('background-color', '#ff8888');
      self.selectedResourceId = $(this).attr('id');
    });
  },

  activateMatchButton: function() {
    var self = this;

    $('#' + this.matchButtonCSSId).click(function() {
      // if a resource is highlighted, attempt to add selected paths
      if (self.selectedResourceId) {
        var selectedPaths = [];
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

        // if any paths have been selected
        if(selectedPaths.length) {
          selectedPaths.forEach(function(item) {
            $('#' + item.id + ' > input').attr('disabled', 'disabled');
            var $newMatchEl = $(self.matchItemTemplate({
              'index': self.matchIndex,
              'path': item.path
            }));
            $newMatchEl.hide();
            $('#' + self.matchPaneCSSId).append($newMatchEl);
            $newMatchEl.fadeIn('fast');
            (function(index, pathId) {
              $('#match_delete_' + self.matchIndex).click(function() {
                $('#' + pathId + ' > input').removeAttr('disabled');
                $('#match_' + index).remove();
              });
            })(self.matchIndex, item.id)
            self.matchIndex++;
          });
        }
      }
    });
  }
});
