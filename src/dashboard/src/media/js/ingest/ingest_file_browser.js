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

var enableElements = function(cssSelectors) {
  for (var index in cssSelectors) {
    $(cssSelectors[index]).removeAttr('disabled');
  }
};

var disableElements = function(cssSelectors) {
  for (var index in cssSelectors) {
    $(cssSelectors[index]).attr('disabled', 'disabled');
  }
};

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

        // enable/disable arrange panel action buttons
        if (explorer.id == 'originals') {
          enableOrDisableOriginalsPanelActionButtons(explorer);
        }

        // enable/disable arrange panel action buttons
        if (explorer.id == 'arrange') {
          enableOrDisableArrangePanelActionButtons(explorer);
        }
      }
    }
  }

  function enableOrDisableOriginalsPanelActionButtons(originals) {
    var selectedType = originals.getTypeForCssId(originals.selectedEntryId);

    // enable/disable hide button
    if (typeof originals.selectedEntryId !== 'undefined') {
      enableElements(['#originals_hide_button']);
    } else {
      disableElements(['#originals_hide_button']);
    }

    // enable/disable buttons for actions that only work with files
    if (typeof originals.selectedEntryId !== 'undefined' && selectedType == 'file') {
      enableElements(['#open_originals_file_button']);
    } else {
      disableElements(['#open_originals_file_button']);
    }
  }

  function enableOrDisableArrangePanelActionButtons(arrange) {
    var selectedType = arrange.getTypeForCssId(arrange.selectedEntryId);

    // enable/disable delete button
    if (typeof arrange.selectedEntryId !== 'undefined') {
      enableElements(['#arrange_delete_button']);
    } else {
      disableElements(['#arrange_delete_button']);
    }

    // enable/disable create SIP button
    if (selectedType == 'directory') {
      enableElements(['#arrange_create_sip_button']);
    } else {
      disableElements(['#arrange_create_sip_button']);
    }

    // enable/disable metadata button
    if (typeof arrange.selectedEntryId !== 'undefined') {
      enableElements(['#arrange_edit_metadata_button']);
    } else {
      disableElements(['#arrange_edit_metadata_button']); 
    }

    // enable/disable create directory button
    // (if nothing is selected, it'll create in top level)
    if (typeof arrange.selectedEntryId === 'undefined' || selectedType == 'directory') {
      enableElements(['#arrange_create_directory_button']);
    } else {
      disableElements(['#arrange_create_directory_button']);
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
    var actionUrlPath, source
        arrangeDir = '/'+Base64.decode(move.self.structure.name)

    // do a move if drag and drop occurs within the arrange pane
    if (
      move.droppedPath.indexOf(arrangeDir) == 0
      && move.containerPath.indexOf(arrangeDir) == 0
    ) {
      // arrange -> arrange
      actionUrlPath = '/filesystem/move_within_arrange/';
      source = move.self.getByPath(move.droppedPath)
    } else {
      // originals -> arrange
      actionUrlPath = '/filesystem/copy_to_arrange/';
      // TODO don't use global if possible
      source = originals.getByPath(move.droppedPath)
    }

    var destination = move.self.getByPath(move.containerPath);
    // Add trailing / to directories
    if (source.type() == 'directory') {
      move.droppedPath+='/'
    }
    if (typeof destination == 'undefined') {
      // Moving into the parent directory arrange/
      // Error if source is a file
      if (source.type() != 'directory') {
        move.self.alert('Error', "Files must go in a SIP, not the parent directory.");
      }
      move.containerPath = arrangeDir+'/'
    } else if (destination.type() == 'directory') {
      move.containerPath+='/'
    }

    $.post(
      actionUrlPath,
      {
        filepath: Base64.encode(move.droppedPath),
        destination: Base64.encode(move.containerPath)
      },
      function(result) {
        if (result.error == undefined) {
          move.self.idle();
          move.self.render();
          $('#search_submit').click(); // Fetches from backlog again and renders it
        } else {
          alert(result.message);
          move.self.idle();
        }
      }
    );
  }

  var originals = new FileExplorer({
    el: $('#originals'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    entryClickHandler: backlogBrowserEntryClickHandler,
    nameClickHandler: backlogBrowserEntryClickHandler,
    // Data will be populated by backlog.js when a search is conducted
  });

  originals.structure = {
    'name': Base64.encode('originals'),
    'parent': '',
    'children': []
  };

  originals.itemsPerPage = 10;
  originals.moveHandler = moveHandler;
  originals.options.actionHandlers = [];
  originals.render();
  enableOrDisableOriginalsPanelActionButtons(originals);

  var arrange = new FileExplorer({
    el: $('#arrange'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    entryClickHandler: backlogBrowserEntryClickHandler,
    nameClickHandler: backlogBrowserEntryClickHandler,
    ajaxDeleteUrl: '/filesystem/delete/arrange/',
    ajaxChildDataUrl: '/filesystem/contents/arrange/'
  });

  arrange.structure = {
    'name': Base64.encode('arrange'),
    'parent': '',
    'children': []
  };

  arrange.itemsPerPage = 10;
  arrange.options.actionHandlers = [];
  arrange.moveHandler = moveHandler;
  arrange.render();
  enableOrDisableArrangePanelActionButtons(arrange);

  // search results widget
  var originals_search_results = new fileBrowser.EntryList({
    el: $('#originals_search_results'),
    moveHandler: moveHandler,
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html(),
    itemsPerPage: 20
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
  // Monkey-patch entry toggling logic to allow auto-search of backlog
  (function(originalToggleDirectoryLogic) {
    var backlogSearched = false;

    fileBrowser.EntryView.prototype.toggleDirectory = function($el) {
      var result = originalToggleDirectoryLogic.apply(this, arguments);

      // if toggling in the original panels, check to see if backlog entries have been
      // added to it yet and, if not, perform search
      if (this.container.id == 'originals' &&
        this.container.structure.children.length == 0 &&
        backlogSearched == false
      ) {
        backlogSearched = true;
        $('#search_submit').click();
      }

      return result;
    };
  })(fileBrowser.EntryView.prototype.toggleDirectory);

  var browsers = setupBacklogBrowser();

  originals_browser = browsers['originals'];
  arrange_browser = browsers['arrange'];

  originals_browser.display_data = function(data) {
    // Accept and display data from an external source
    // Assumes it is properly formatted already
    this.structure.children = data;
    // Open top level folder
    this.openFolder($('#'+this.id+'__'+Base64.decode(this.structure.name)))
    this.render();
  }

  $('#arrange_edit_metadata_button').click(function() {
    // if metadata button isn't disabled, execute
    if (typeof $('#arrange_edit_metadata_button').attr('disabled') === 'undefined') {
      if (typeof arrange_browser.selectedEntryId === 'undefined') {
        arrange_browser.alert('Edit metadata', 'Please select a directory or file to edit.');
        return;
      }

      var path = arrange_browser.getPathForCssId(arrange_browser.selectedEntryId);

      directoryMetadataForm.show(path, function(levelOfDescription) {
        var entry = arrange_browser.getByPath(path);
        entry.set({'levelOfDescription': levelOfDescription});
        arrange_browser.render();
      });
    }
  });

  $('#arrange_create_directory_button').click(function() {
    // if create directory button isn't disabled, execute
    if (typeof $('#arrange_create_directory_button').attr('disabled') === 'undefined') {
      var selectedType = arrange_browser.getTypeForCssId(arrange_browser.selectedEntryId);

      if (selectedType != 'directory' && typeof arrange_browser.selectedEntryId !== 'undefined') {
        arrange_browser.alert('Create Directory', "You can't create a directory in a file.");
      } else {
        var path = prompt('Name of new directory?');

        if (path) {
          var path_root = arrange_browser.getPathForCssId(arrange_browser.selectedEntryId) || '/' + Base64.decode(arrange_browser.structure.name)
            , relative_path = path_root + '/' + path;

          $.ajax({
            url: '/filesystem/create_directory_within_arrange/',
            type: 'POST',
            async: false,
            cache: false,
            data: {
              path: Base64.encode(relative_path)
            },
            success: function(results) {
              arrange_browser.dirView.model.addDir({'name': path});
              arrange_browser.render();
            },
            error: function(results) {
              originals_browser.alert('Error', results.message);
            }
          });
        }
      }
    }
  });

  $('#arrange_delete_button').click(function() {
    if (typeof arrange_browser.selectedEntryId === 'undefined') {
      arrange_browser.alert('Delete', 'Please select a directory or file to delete.');
      return;
    }
    var path = arrange_browser.getPathForCssId(arrange_browser.selectedEntryId)
      , type = arrange_browser.getTypeForCssId(arrange_browser.selectedEntryId);

    arrange_browser.confirm(
      'Delete',
      'Are you sure you want to delete this directory or file?',
      function() {
        if( type == 'directory') {
          path += '/'
        }
        arrange_browser.deleteEntry(path, type);
        arrange_browser.selectedEntryId = undefined;
        $('#search_submit').click();
      }
    );
  });

  // Hide the selected object
  $('#originals_hide_button').click(function () {
    // Have to hide all its children too or weird behaviour
    $('#' + originals_browser.selectedEntryId).next().hide();
    $('#' + originals_browser.selectedEntryId).hide();
  });

  // create SIP button functionality
  $('#arrange_create_sip_button').click(function() {
    // if create SIP button isn't disabled, execute
    if (typeof $('#arrange_create_sip_button').attr('disabled') === 'undefined') {

      if (typeof arrange_browser.selectedEntryId === 'undefined') {
        arrange_browser.alert('Create SIP', 'Please select a directory before creating a SIP.');
        return
      }
      var entryDiv = $('#' + arrange_browser.selectedEntryId)
        , path = arrange_browser.getPathForCssId(arrange_browser.selectedEntryId)
        , entryObject = arrange_browser.getByPath(path)

      if (entryObject.type() != 'directory') {
        arrange_browser.alert('Create SIP', 'SIPs can only be created from directories, not files.')
        return
      }

      arrange_browser.confirm(
        'Create SIP',
        'Are you sure you want to create a SIP?',
        function() {
          $('.activity-indicator').show();
          $.post(
            '/filesystem/copy_from_arrange/',
            {filepath: Base64.encode(path+'/')},
            function(result) {
              $('.activity-indicator').hide();
              var title = (result.error) ? 'Error' : ''
              arrange_browser.alert(
                title,
                result.message
              )
              if (!result.error) {
                $(entryDiv).next().hide()
                $(entryDiv).hide()
              }
            }
          )
        }
      )
    }
  });

  var createOpenHandler = function(buttonCssSelector, browser) {
      return function() {
        // if view button isn't disabled, execute
        if (typeof $(buttonCssSelector).attr('disabled') === 'undefined') {
          if (typeof browser.selectedEntryId === 'undefined') {
            browser.alert('Error', 'Please specifiy a file to view.');
          } else {
            var entryDiv = $('#' + browser.selectedEntryId)
               , path = browser.getPathForCssId(browser.selectedEntryId)
               , type = browser.getTypeForCssId(browser.selectedEntryId);

            if (type == 'directory') {
              browser.alert('Error', 'Please specifiy a file to view.');
            } else {
              window.open(
                '/filesystem/download_ss/?filepath=' + encodeURIComponent(Base64.encode(path)),
                '_blank'
              );
            }
          }
        }
      };
  };

  // open originals file button functionality
  $('#open_originals_file_button').click(createOpenHandler('#open_originals_file_button', originals_browser));
});
