var ATKMatcherView = Backbone.View.extend({
  initialize: function(options) {
    this.objectPaths     = options.objectPaths || alert('objectPaths required.');
    this.resourceData    = options.resourceData || alert('resourceData required.');
    this.objectPaneCSSId = options.objectPaneCSSId || alert('objectPaneCSSId required.');
    this.resourcePaneCSSId = options.resourcePaneCSSId || alert('resourcePaneCSSId required.');

    this.matcherLayoutTemplate  = _.template(options.matcherLayoutTemplate);
    this.objectPathTemplate     = _.template(options.objectPathTemplate);
    this.resourceItemTemplate   = _.template(options.resourceItemTemplate);
  },

  render: function() {
    $(this.el).append(this.matcherLayoutTemplate());

    this.renderObjectPaths();
    this.renderResourceData(this.resourceData);
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
        'padding': padding,
        'title':   resourceData.title
      })
    );

    var self = this;

    if (resourceData.children) {
      resourceData.children.forEach(function(child) {
        self.renderResourceData(child, level + 1);
      });
    }
  }
});
