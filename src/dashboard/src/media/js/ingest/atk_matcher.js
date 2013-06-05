var ATKMatcherView = Backbone.View.extend({
  initialize: function(options) {
    this.objectPaths     = options.objectPaths || alert('objectPaths required.');
    this.resourceData    = options.resourceData || alert('resourceData required.');
    this.objectPaneCSSId = options.objectPaneCSSId || alert('objectPaneCSSId required.');
    this.resourcePaneCSSId = options.resourcePaneCSSId || alert('resourcePaneCSSId required.');

    /*
    this.form_layout_template = _.template(options.form_layout_template);
    */
  },

  render: function() {
    // add and render object pane
    $(this.el).append('<div id="' + this.objectPaneCSSId + '"></div>');
    this.renderObjectPaths();

    // add and render resource data pane
    this.renderResourceData(this.resourceData);
  },

  renderObjectPaths: function() {
    this.objectPaths.forEach(function(path) {
      $('#' + this.objectPaneCSSId).append('<p>' + path + '</p>');
    });
  },

  renderResourceData: function(resourceData, level) {
    level = level || 0;
    $('#' + this.resourcePaneCSSId).append('<p>');
    for (var index = 0; index < level; index++) {
      $('#' + this.resourcePaneCSSId).append('&nbsp;&nbsp;');
    }
    $('#' + this.resourcePaneCSSId).append(resourceData.title);
    $('#' + this.resourcePaneCSSId).append('</p>');

    var self = this;
    if (resourceData.children) {
      resourceData.children.forEach(function(child) {
console.log('poo');
        self.renderResourceData(child, level + 1);
      });
    }
  }
});
