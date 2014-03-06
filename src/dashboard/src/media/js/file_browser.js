/*
This file is part of Archivematica.

Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>

Archivematica is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Archivematica is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
*/

var FileExplorer = fileBrowser.FileExplorer.extend({

  initialize: function() {
    this.structure = {};
    this.options.closeDirsByDefault = true;

    this.itemsPerPage = 50;

    this.render();

    var self = this;

    // allow use of contents paths with augmented data, if desired
    if (typeof this.options.directoryContentsURLPath != 'undefined') {
      this.directoryContentsURLPath = this.options.directoryContentsURLPath;
    } else {
      this.directoryContentsURLPath = '/filesystem/contents/';
    }

    // allow option use of a child data URL for larger directories
    if (typeof this.options.ajaxChildDataUrl != 'undefined') {
      this.ajaxChildDataUrl = this.options.ajaxChildDataUrl;
    }

    this.ajaxDeleteUrl = this.options.ajaxDeleteUrl || '/filesystem/delete/';

    this.eventClickHandler = this.options.eventClickHandler;

    if (this.options.actionHandlers == undefined) {
      this.options.actionHandlers = [];
    }

    var self = this;
    this.options.actionHandlers.push({ 
        name: 'Delete', 
        description: 'Delete file or directory', 
        iconHtml: "<img src='/media/images/delete.png' />", 
        logic: function(result) { 
          self.confirm(
            'Delete',
            'Are you sure you want to delete this directory or file?',
            function() {
              self.deleteEntry(result.path, result.type);
            }
          );
        }
    });

    this.id = $(this.el).attr('id'); 
    //this.initDragAndDrop();
  },

  deleteEntry: function(path, type) {
    var self = this;
    $.post(
      this.ajaxDeleteUrl,
      {filepath: Base64.encode(path)},
      function(response) {
        if (response.error) {
          self.alert(
            'Delete',
            response.message
          );
        }

        if (self.ajaxChildDataUrl) {
          self.render();
        } else {
          self.refresh();
        }
      }
    );
  },

  refresh: function(path) {
    //$(this.el).empty();
    this.busy();

    if (path != undefined)
    {
      this.path = path;
    }

    var url = (this.path != undefined)
      ? this.directoryContentsURLPath + '?path=' + encodeURIComponent(this.path)
      : this.directoryContentsURLPath;

    var self = this;

    $.ajax({
      url: url,
      async: false,
      cache: false,
      success: function(results) {
        self.structure = results;
        self.render();
        self.initDragAndDrop();
        self.idle();
      }
    });
  },

  moveHandler: function(move) {
    if (move.allowed) {
      move.self.busy();
      $('#message').text(
        'Dropped ID ' + move.droppedPath + ' onto ' + move.containerPath
      );
      setTimeout(function() {
        move.self.idle();
        $('#message').text('');
      }, 2000);
    } else {
      alert("You can't move a directory into its subdirectory.");
    }
  },

  addSource: function(fileExplorer, path) {
    var self = this;
    $.post(
      '/administration/sources/json/',
      {path: path},
      function(response) {
        self.alert(
          'Add source directory',
          response.message
        );
        self.updateSources();
      }
    );
  },

  deleteSource: function(id) {
    var self = this;
    this.confirm(
      'Delete source directory',
      'Are you sure you want to delete this?',
      function() {
        $.post(
          '/administration/sources/delete/json/' + id + '/',
          {},
          function(response) {
            self.alert(
              'Delete source directory',
              response.message
            );
            self.updateSources();
          }
        );
      }
    );
  },

  updateSources: function(cb) {
    var self = this;
    $.get('/administration/sources/json/' + '?' + new Date().getTime(), function(results) {
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
