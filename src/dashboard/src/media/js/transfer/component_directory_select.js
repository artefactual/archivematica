var DirectorySelectorView = fileBrowser.FileExplorer.extend({

  initialize: function() {
    this.structure = {};
    this.options.closeDirsByDefault = true;
    this.options.entryDisplayFilter = function(entry) {
      // if a file and not a ZIP file, then hide
      if (
        entry.children == undefined
        && entry.attributes.name.toLowerCase().indexOf('.zip') == -1
      ) {
          return false;
      }
      return true;
    };

    this.render();

    this.options.actionHandlers = []
  }
});

function createDirectoryPicker(baseDirectory, modalCssId, targetCssId) {
  var url = '/filesystem/contents/?path=' + encodeURIComponent(baseDirectory)

  var selector = new DirectorySelectorView({
    el: $('#explorer'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html()
  });

  selector.options.actionHandlers.push({
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

      $transferPathEl.html('/' + result.path);
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
  });

  selector.busy();

  $.get(url, function(results) {
    selector.structure = results;
    selector.render();

    selector.idle();
  });
}
