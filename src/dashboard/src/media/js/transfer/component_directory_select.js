function createDirectoryPicker(baseDirectory, modalCssId, targetCssId) {
  var selector = new DirectoryPickerView({
    ajaxChildDataUrl: '/filesystem/children/',
    el: $('#explorer'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html()
  });

  selector.structure = {
    'name': baseDirectory.replace(/\\/g,'/').replace( /.*\//, '' ),      // parse out path basename
    'parent': baseDirectory.replace(/\\/g,'/').replace(/\/[^\/]*$/, ''), // parse out path directory
    'children': []
  };

  selector.options.entryDisplayFilter = function(entry) {
    // if a file and not a ZIP file, then hide
    if (
      entry.children == undefined
      && entry.attributes.name.toLowerCase().indexOf('.zip') == -1
    ) {
        return false;
    }
    return true;
  };

  selector.options.actionHandlers = [{
    name: 'Select',
    description: 'Select',
    iconHtml: 'Add',
    logic: function(result) {
      var $transferPathRowEl = $('<div></div>')
        , $transferPathEl = $('<span class="transfer_path"></span>')
        , $transferPathDeleteRl = $('<span style="margin-left: 1em;"><img src="/media/images/delete.png" /></span>');

      $transferPathDeleteRl.click(function() {
        $transferPathRowEl.remove();
      });

      $transferPathEl.html(result.path);
      $transferPathRowEl.append($transferPathEl);
      $transferPathRowEl.append($transferPathDeleteRl);
      $('#' + targetCssId).append($transferPathRowEl);
      $('#' + modalCssId).remove();

      // tiger stripe transfer paths
      $('.transfer_path').each(function() {
        $(this).parent().css('background-color', '');
      });
      $('.transfer_path:odd').each(function() {
        $(this).parent().css('background-color', '#eee');
      });
    }
  }];

  selector.render();
}
