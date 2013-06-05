var ATKMatcherView = Backbone.View.extend({
  initialize: function(options) {
    this.objectPaths     = options.objectPaths || alert('objectPaths required.');
    this.resourceData    = options.resourceData || alert('resourceData required.');

    this.objectPaneCSSId   = options.objectPaneCSSId || alert('objectPaneCSSId required.');
    this.resourcePaneCSSId = options.resourcePaneCSSId || alert('resourcePaneCSSId required.');
    this.matchButtonCSSId  = options.matchButtonCSSId || alert('matchButtonCSSId required.');
    this.matchPaneCSSId    = options.matchPaneCSSId || alert('matchPaneCSSId required.');

    this.matcherLayoutTemplate  = _.template(options.matcherLayoutTemplate);
    this.objectPathTemplate     = _.template(options.objectPathTemplate);
    this.resourceItemTemplate   = _.template(options.resourceItemTemplate);
    this.matchItemTemplate      = _.template(options.matchItemTemplate);

    this.resourceIndex = 0;
    this.selectedResourceId = false;
    this.matchIndex = 0;
  },

  render: function() {
    $(this.el).append(this.matcherLayoutTemplate());

    this.renderObjectPaths();
    this.renderResourceData(this.resourceData);

    var self = this;
    $('#' + this.matchButtonCSSId).click(function() {
      // if a resource is highlighted, attempt to add selected paths
      if (self.selectedResourceId) {
        var selectedPaths = [];
        $('#' + self.objectPaneCSSId + ' > div').each(function() {
          if ($(this).children('input').attr('checked') == 'checked') {
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
            self.matchIndex++;
          });
        }
      }
    });

    $('#resource_pane > div').click(function() {
      $('#resource_pane > div').css('background-color', '');
      $(this).css('background-color', 'red');
      self.selectedResourceId = $(this).attr('id');
    });
  },

  renderObjectPaths: function() {
    var self = this,
        index = 0;

    this.objectPaths.forEach(function(path) {
      $('#' + self.objectPaneCSSId).append(
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

    $('#' + this.resourcePaneCSSId).append(
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
  }
});
