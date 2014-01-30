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
function setupBacklogBrowser() {
  var backlogBrowserEntryClickHandler = function(event) {
    if (typeof event.data != 'undefined') {
      var explorer = event.data.self.container
        , explorerId = explorer.id

        var entryEl = this
        , entryId = $(this).attr('id')
        , borderCssSpec = '1px solid red';

      if (explorer.selectedEntryId == entryId) {
        // un-highlight selected entry
        $(entryEl).css('border', '');

        // remove selected entry
        explorer.selectedEntryId = undefined;
      } else {
        // remove highlighting of existing entries
        $('#' + explorerId).find('.backbone-file-explorer-entry').css('border', '');

        // highlight selected entry
        $(entryEl).css('border', borderCssSpec);

        // change selected entry
        explorer.selectedEntryId = entryId;
      }
    }
  }

  function moveHandler(move) {
    // don't allow moving anything into the originals directory
    if (move.self.id == 'originals') {
      move.self.alert('Error', "You can't copy into the originals directory.");
      return;
    }
    if (!move.allowed) {
      move.self.alert('Error', "You can't move a directory into its subdirectory.");
      return;
    }
    // move.self is the arrange browser
    move.self.busy();

    // determine whether a move or copy should be performed
    var actionUrlPath,
        arrangeDir = '/'+move.self.structure.name;

    // do a move if drag and drop occurs within the arrange pane
    if (
      move.droppedPath.indexOf(arrangeDir) == 0
      && move.containerPath.indexOf(arrangeDir) == 0
    ) {
      actionUrlPath = '/filesystem/move_within_arrange/';
      // Add trailing / to directories
      if (move.self.getByPath(move.droppedPath).type() == 'directory') {
        move.droppedPath+='/'
      }
    } else {
      actionUrlPath = '/filesystem/copy_to_arrange/';
      // TODO how to get directory info from original??
    }

    var destination = move.self.getByPath(move.containerPath);
    if (typeof destination == 'undefined') {
      // FIXME error if source is a file
      // Moving into the parent directory arrange/
      move.containerPath = arrangeDir+'/'
    } else if (destination.type() == 'directory') {
      move.containerPath+='/'
    } else {
      move.self.alert('Error', "You cannot drag and drop onto a file.");
      move.self.idle();
      return;
    }

    $.post(
      actionUrlPath,
      {
        filepath: move.droppedPath,
        destination: move.containerPath
      },
      function(result) {
        if (result.error == undefined) {
          move.self.idle();
          move.self.render();
        } else {
          alert(result.message);
          move.self.idle();
        }
      }
    );
  }

  /*
  TODO: figure out how to augment AJAX child data with accession ID...

  Was using directoryContentsURLPath: '/filesystem/contents/originals/' but that
  doesn't scale. Figure out new way and get rid of /filesystem/contents/originals/
  endpoint.
  */
  var originals = new FileExplorer({
    el: $('#originals'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    entryClickHandler: backlogBrowserEntryClickHandler,
    nameClickHandler: backlogBrowserEntryClickHandler,
    ajaxChildDataUrl: '/filesystem/contents/originals/'
  });

  originals.structure = {
    'name': 'originals',
    'parent': '',
    'children': []
  };

  originals.itemsPerPage = 10;
  originals.moveHandler = moveHandler;
  originals.options.actionHandlers = [];
  originals.render();

  var arrange = new FileExplorer({
    el: $('#arrange'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    entryClickHandler: backlogBrowserEntryClickHandler,
    nameClickHandler: backlogBrowserEntryClickHandler,
    ajaxChildDataUrl: '/filesystem/contents/arrange/'
  });

  arrange.structure = {
    'name': 'arrange',
    'parent': '',
    'children': []
  };

  arrange.itemsPerPage = 10;
  arrange.options.actionHandlers = [];
  arrange.moveHandler = moveHandler;
  arrange.render();

  // search results widget
  var originals_search_results = new fileBrowser.EntryList({
    el: $('#originals_search_results'),
    moveHandler: moveHandler,
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    itemsPerPage: 20
  });

  // define search behavior
  function searchOriginals() {
    $('#originals').hide();
    $('#originals_controls').hide();

    originals_search_results.currentPage = 0;

    originals_search_results.entries = originals.findEntry(function(entry) {
      var query = $('#originals_query').val(),
          hit = false;

      // check if query matches name
      hit = entry.get('name').toLowerCase().indexOf(query.toLowerCase()) != -1;

      // if query doesn't match name, check if other field matches
      if (hit == false && typeof entry.get('data') != 'undefined') {

        // if entry has accession ID data, see if it matches          
        if (typeof entry.get('data')['accessionId'] != 'undefined') {
          hit = entry.get('data')['accessionId'].indexOf(query) != -1;
        }
      }

      return hit;
    });

    if (originals_search_results.entries.length > 0) {
      originals_search_results.render();
      originals_search_results.initDragAndDrop();
    } else {
      $('#originals_search_results').html('No results.');
    }

    $('#originals_search_results').show();
  }

  // search if user presses "enter"
  $('#originals_search_form').submit(function(e) {
    e.preventDefault(e);
    searchOriginals();
  });

  // search if use clicks "search" button
  $('#originals_search_button').click(function() {
    searchOriginals();
  });

  // reset search form and hide search results widget
  $('#originals_search_reset_button').click(function() {
    $('#originals_query').val('');
    $('#originals_search_results').hide();
    $('#originals').show();
    $('#originals_controls').show();
  });

  return {
    'originals': originals,
    'arrange': arrange
  };
}

// spawn browsers
var originals_browser,
    arrange_browser;

$(document).ready(function() {
  var arrange_directory = shared_dir_location_path + '/arrange',
      originals_directory = shared_dir_location_path + '/www/AIPsStore/transferBacklog/originals';

  browsers = setupBacklogBrowser();

  originals_browser = browsers['originals'];
  arrange_browser = browsers['arrange'];

  $('#arrange_create_directory_button').click(function() {
    var path = prompt('Name of new directory?');

    if (path != '') {
      var path_root = arrange_browser.getPathForCssId(arrange_browser.selectedEntryId)
        , relative_path = path_root + '/' + path;

      $.ajax({
        url: '/filesystem/create_directory_within_arrange/',
        type: 'POST',
        async: false,
        cache: false,
        data: {
          path: relative_path
        },
        success: function(results) {
          var directory = arrange_browser.getByPath(path_root);
          directory.addDir({'name': path});
          arrange_browser.render();
          arrange_browser.alert('Create directory', results.message);
        },
        error: function(results) {
          originals_browser.alert('Error', results.message);
        }
      });
    }
  });

  // delete button functionality
  var createDeleteHandler = function(browser, directory) {
    return function() {
      if (typeof browser.selectedEntryId === 'undefined') {
        browser.alert('Delete', 'Please select a directory to delete.');
      } else {
        // only allow top-level directories to be deleted
        var delete_path = browser.getPathForCssId(browser.selectedEntryId);

        if (delete_path.split('/').length != directory.split('/').length + 1) {
          browser.alert('Delete', 'You can only delete top-level directories.');
        } else {
          var path = browser.getPathForCssId(browser.selectedEntryId)
            , type = browser.getTypeForCssId(browser.selectedEntryId);

          browser.confirm(
            'Delete',
            'Are you sure you want to delete this directory or file?',
            function() {
              browser.deleteEntry(path, type);
            }
          );
        }
      }
    };
  };

  $('#arrange_delete_button').click(createDeleteHandler(arrange_browser, arrange_directory));
  $('#originals_delete_button').click(createDeleteHandler(originals_browser, originals_directory));

  // create SIP button functionality
  $('#arrange_create_sip_button').click(function() {
    if (typeof arrange_browser.selectedEntryId === 'undefined') {
      arrange_browser.alert('Create SIP', 'Please select a directory before creating a SIP.');
    } else {
      var entryDiv = $('#' + arrange_browser.selectedEntryId)
        , path = arrange_browser.getPathForCssId(arrange_browser.selectedEntryId);

      arrange_browser.confirm(
        'Create SIP',
        'Are you sure you want to create a SIP?',
        function() {
          $.post(
            '/filesystem/copy_from_arrange/',
            {filepath: path},
            function(result) {
              var title = (result.error) ? 'Error' : '';
              arrange_browser.alert(
                title,
                result.message
              );
              if (!result.error) {
                $(entryDiv).next().hide();
                $(entryDiv).hide();
              }
            }
          );
        }
      );
    }
  });

  var createOpenHandler = function(browser) {
      return function() {
        var entryDiv = $('#' + browser.selectedEntryId)
           , path = browser.getPathForCssId(browser.selectedEntryId)
           , type = browser.getTypeForCssId(browser.selectedEntryId);

        if (type == 'directory') {
          browser.alert('Error', 'You can not open a directory.');
        } else {
          window.open(
            '/filesystem/download?filepath=' + encodeURIComponent(path),
            '_blank'
          );
        }
      };
  };

  // open originals file button functionality
  $('#open_originals_file_button').click(createOpenHandler(originals_browser));

  // open arrange file button functionality
  $('#open_arrange_file_button').click(createOpenHandler(arrange_browser));
});
