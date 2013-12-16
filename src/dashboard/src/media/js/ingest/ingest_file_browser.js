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
function setupBacklogBrowser(originalsDirectory, arrangeDirectory) {
  var backlogBrowserEntryClickHandler = function(event) {
    if (typeof event.data != 'undefined') {
      var explorer = event.data.self.explorer
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
    if (move.self.id != 'originals') {
      if (move.allowed) {
        move.self.busy();

        // determine whether a move or copy should be performed
        var actionUrlPath,
            arrangeDir = 'var/archivematica/sharedDirectory/arrange/';

        // do a move if drag and drop occurs within the arrange
        // pane
        if (
          move.droppedPath.indexOf(arrangeDir) == 0
          && move.containerPath.indexOf(arrangeDir) == 0
        ) {
          actionUrlPath = '/filesystem/move_within_arrange/';
        } else {
          actionUrlPath = '/filesystem/copy_to_arrange/';
        }

        $.post(
          actionUrlPath,
          {
            filepath: move.droppedPath,
            destination: move.containerPath
          },
          function(result) {
            if (result.error == undefined) {
              // TODO: remove from DOM
              arrange.refresh(arrangeDirectory);
            } else {
              alert(result.message);
              move.self.idle();
            }
          }
        );
      } else {
        move.self.alert('Error', "You can't move a directory into its subdirectory.");
      }
    } else {
      move.self.alert('Error', "You can't copy into the originals directory.");
    }
  }

  var originals = new FileExplorer({
    el: $('#originals'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    entryClickHandler: backlogBrowserEntryClickHandler,
    nameClickHandler: backlogBrowserEntryClickHandler
  });

  originals.itemsPerPage = 10;
  originals.moveHandler = moveHandler;
  originals.options.actionHandlers = [];
  originals.refresh(originalsDirectory);

  var arrange = new FileExplorer({
    el: $('#arrange'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    entryClickHandler: backlogBrowserEntryClickHandler,
    nameClickHandler: backlogBrowserEntryClickHandler
  });

  arrange.itemsPerPage = 10;
  arrange.options.actionHandlers = [];
  arrange.moveHandler = moveHandler;
  arrange.refresh(arrangeDirectory);

  return {
    'originals': originals,
    'arrange': arrange
  };
}

// spawn browsers
var originals_browser,
    arrange_browser;

$(document).ready(function() {
  var arrange_directory = '/var/archivematica/sharedDirectory/arrange'
    , originals_directory = '/var/archivematica/sharedDirectory/www/AIPsStore/transferBacklog/originals';

  browsers = setupBacklogBrowser(
    originals_directory,
    arrange_directory
  );
  originals_browser = browsers['originals'];
  arrange_browser = browsers['arrange'];

  // delete button functionality
  var createDeleteHandler = function(browser, directory) {
    return function() {
      if (typeof browser.selectedEntryId === 'undefined') {
        browser.alert('Delete', 'Please select a directory to delete.');
      } else {
        // only allow top-level directories to be deleted
        var delete_path = browser.getPathForCssId(browser.selectedEntryId);
        if (delete_path.split('/').length >= directory.split('/').length + 1) {
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

  // open originals file button functionality
  $('#open_originals_file_button').click(function() {
    var entryDiv = $('#' + originals_browser.selectedEntryId)
      , path = originals_browser.getPathForCssId(originals_browser.selectedEntryId);

    window.open(
      '/filesystem/download?filepath=' + encodeURIComponent(path),
      '_blank'
    );
  });

  // open arrange file button functionality
  $('#open_arrange_file_button').click(function() {
    var entryDiv = $('#' + arrange_browser.selectedEntryId)
      , path = arrange_browser.getPathForCssId(arrange_browser.selectedEntryId);

    window.open(
      '/filesystem/download?filepath=' + encodeURIComponent(path),
      '_blank'
    );
  });
});
