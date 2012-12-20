var DirectoryPickerView = fileBrowser.FileExplorer.extend({

  initialize: function() {
    this.structure                  = {};
    this.options.closeDirsByDefault = true;

    // hide all files
    this.options.entryDisplayFilter = function(entry) {
      if (entry.children == undefined) {
          return false;
      }
      return true;
    };

    this.ajaxChildDataUrl = this.options.ajaxChildDataUrl;
    this.ajaxSelectedDirectoryUrl = this.options.ajaxSelectedDirectoryUrl;
    this.ajaxAddDirectoryUrl = this.options.ajaxAddDirectoryUrl;
    this.ajaxDeleteDirectoryUrl = this.options.ajaxDeleteDirectoryUrl;

    this.render();

    var self = this;
    this.options.actionHandlers = [ 
      { 
        name: 'Select', 
        description: 'Select directory', 
        iconHtml: 'Add', 
        logic: function(result) { 
          self.addDirectory(self, result.path); 
        } 
      } 
    ]; 
  },

  addDirectory: function(fileExplorer, path) {
    var self = this;
    $.post(
      this.ajaxAddDirectoryUrl,
      {path: path},
      function(response) {
        self.updateSelectedDirectories();
      }
    );
  },

  deleteSource: function(id) {
    var self = this;
    this.confirm(
      'De-select directory',
      'Are you sure you want to de-select this?',
      function() {
        $.post(
          self.ajaxDeleteDirectoryUrl + id + '/',
          {},
          function(response) {
            self.updateSelectedDirectories();
          }
        );
      }
    );
  },

  updateSelectedDirectories: function(cb) {
    var self = this;
    $.get(this.ajaxSelectedDirectoryUrl + '?' + new Date().getTime(), function(results) {
      tableTemplate = _.template($('#template-source-directory-table').html());
      rowTemplate   = _.template($('#template-source-directory-table-row').html());

      $('#directories').empty();
      $('#directories').off('click');

      if (results['directories'].length) {
        var rowHtml = '';

        for(var index in results['directories']) {
          rowHtml += rowTemplate({
            id:   results.directories[index].id,
            path: results.directories[index].path
          });
        }

        $('#directories').append(tableTemplate({rows: rowHtml}));

        $('#directories').on('click', 'a', function() {
          var directoryId = $(this).attr('id').replace('directory_', '');
          self.deleteSource(directoryId);
        });
      }

      if (cb != undefined) {
        cb();
      }
    });
  },

  alert: function(title, message) {
    $('<div class="task-dialog">' + message + '</div>')
      .dialog({
        title: title,
        width: 200,
        height: 200,
        modal: true,
        buttons: [
          {
            text: 'OK',
            click: function() {
              $(this).dialog('close');
            }
          }
        ]
      });
  },

  confirm: function(title, message, logic) {
    $('<div class="task-dialog">' + message + '</div>')
      .dialog({
        title: title,
        width: 200,
        height: 200,
        modal: true,
        buttons: [
          {
            text: 'Yes',
            click: function() {
              $(this).dialog('close');
              logic();
            }
          },
          {
            text: 'Cancel',
            click: function() {
              $(this).dialog('close');
            }
          }
        ]
      });
  }
});
