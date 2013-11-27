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
    var explorer = event.data.self.explorer
      , explorerId = explorer.id
      , entryEl = this
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
      explorer.selectedEntryId = entryId; // $(entryEl).attr('id')
    }
  }

  function moveHandler(move) {
      console.log(move);
    // don't allow dragging stuff from originals directory?
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
              arrange.refresh(arrangeDirectory);
            } else {
              alert(result.message);
              move.self.idle();
            }
          }
        );
      } else {
        alert("You can't move a directory into its subdirectory.");
      }
    } else {
      alert("You can't copy into the originals directory.");
    }
  }

  var originals = new FileExplorer({
    el: $('#originals'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    entryClickHandler: backlogBrowserEntryClickHandler,
    nameClickHandler: backlogBrowserEntryClickHandler
  });

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

  arrange.options.actionHandlers = [];
  arrange.moveHandler = moveHandler;
  arrange.refresh(arrangeDirectory);

  return {
    'originals': originals,
    'arrange': arrange
  };
}
