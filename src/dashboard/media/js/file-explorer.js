(function(exports) {

  /*
   * A patch to indexOf to fix IE8-related issues.
   *
   * See:
   * http://stackoverflow.com/questions/3629183/why-doesnt-indexof-work-on-an-array-ie8
   */
  if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(elt /*, from*/) {
      var len = this.length >>> 0;

      var from = Number(arguments[1]) || 0;
      from = (from < 0)
           ? Math.ceil(from)
           : Math.floor(from);
      if (from < 0)
        from += len;

      for (; from < len; from++) {
        if (from in this &&
            this[from] === elt
        )
          return from;
      }
      return -1;
    };
  }

  /*
   * Data shared by various views. Stores drag-and-drop related bookkeeping
   * data and a map for associating CSS IDs with paths.
   */
  exports.Data = {
    startX: {},
    startY: {},
    mouseX: 0,
    mouseY: 0,
    idPaths: {}
  };

  /*
   * Capture mouse position for drag-and-drop use.
   */
  $(document).mousemove(function(event) {
    exports.Data['mouseX'] = event.pageX;
    exports.Data['mouseY'] = event.pageY;
  });

  /**
   * Default functions for functions used to render paging controls.
   * @constant
   */
  var DEFAULT_PAGING_CONTROL_RENDER_FUNCTIONS = {
    previous: function(itemsPerPage) {
      return $('<span class="backbone-file-explorer-paging-link">Previous ' + itemsPerPage + '</span>');
    },
    next: function(itemsPerPage) {
      return $('<span class="backbone-file-explorer-paging-link">Next ' + itemsPerPage + '</span>');
    },
    separator: function(itemsPerPage) {
      return $('<span class="backbone-file-explorer-paging-link-separator">&nbsp;|&nbsp;</span>');
    }
  };

  /**
   * Backbone model to represent a file entry.
   * @constructor
   */
  exports.File = Backbone.Model.extend({

    // generate id without slashes and replacing periods
    id: function() {
      var path = this.displaypath().replace(/\//g, '_').replace('.', '__');
      return path.replace(/\ /g, '___');
    },

    // Provides a human-readable version of the path, suitable for display.
    // This is used by path() below.
    displaypath: function() {
      parent = this.get('parent');
      name = this.get('name') || '';
      name = Base64.decode(name);
      return (parent !== undefined)
        ? Base64.decode(parent) + '/' + name
        : name;
    },

    // Decode parent and child elements, concatenate them as plaintext,
    // then base64-encode them again for transfer to a server.
    // This is primarily used when querying the storage service.
    path: function() {
      return Base64.encode(this.displaypath());
    },

    type: function() {
      return (this.children == undefined) ? 'file' : 'directory';
    }
  });

  /**
   * Backbone model to represent a directory entry.
   * @constructor
   * @extends File
   */
  exports.Directory = exports.File.extend({
    initialize: function() {
      this.children = [];
      this.cssClass = 'backbone-file-explorer-directory';
    },

    addChild: function(options, Type) {
      var child = new Type(options)
        , parent = this.get('parent');

      // Both parent (if present) and child are still base64-encoded at this point
      name = this.get('name') || '';
      name = Base64.decode(name);
      parent = (parent !== undefined)
        ? Base64.decode(parent) + '/' + name
        : name;
      if (parent) {
        parent = Base64.encode(parent);
      }

      // set ad-hoc properties, if specified
      if (typeof options != 'undefined' && typeof options.properties != 'undefined') {
        for (var property in options.properties) {
          var propertyMap = {};
          propertyMap[property] = options.properties[property];
        }
        child.set(propertyMap);
      }

      child.set({parent: parent});

      this.children.push(child);
      return child;
    },

    addFile: function(options) {
      return this.addChild(options, exports.File);
    },

    addDir: function(options) {
      return this.addChild(options, exports.Directory);
    }
  });

  /**
   * Backbone view for a file or directory entry.
   * @constructor
   */
  exports.EntryView = Backbone.View.extend({

    initialize: function() {
      this.cssIdNamespace = this.options.cssIdNamespace;
      this.model     = this.options.entry;
      this.container = this.options.container;
      this.className = (this.model.children != undefined)
        ? 'backbone-file-explorer-directory'
        : 'directory-file';
      this.template          = this.options.template;
      this.entryClickHandler = this.options.entryClickHandler;
      this.nameClickHandler  = this.options.nameClickHandler;
      this.actionHandlers    = this.options.actionHandlers;
    },

    // template variables for rendering to HTML
    context: function() {
      var context = this.model.toJSON();
      context.className = this.className;
      context.extra = undefined
      if (context['properties'] && context['properties']['display_string']){
        context.extra = '(' + context['properties']['display_string'] + ')'
      }
      return context;
    },

    cssId: function() {
      if (this.cssIdNamespace) {
        return this.cssIdNamespace + '_' + this.model.id();
      } else {
        return this.container.id + '_' + this.model.id();
      }
    },

    toggleDirectory: function($el) {
      $el.next().toggle();
      if ($el.next().is(':visible')) {
        $el.addClass('backbone-file-explorer-directory_open');
      } else {
        $el.removeClass('backbone-file-explorer-directory_open');
      }
    },

    render: function() {
      // The actual path is stored as base64, so it needs to be decoded
      // before being displayed in HTML.
      var context = this.context();
      if (context.name) {
        context.name = Base64.decode(context.name);
      }
      html = this.template(context);

      this.el = $(html);
      $(this.el).addClass(this.className);

      // set CSS ID for entries (used to capture whether directory is
      // open/closed by user between data refreshes, etc.)
      $(this.el).attr('id', this.cssId());

      // If not draggable, add class to that effect
      if (this.model.attributes.not_draggable) {
        $(this.el).addClass('not_draggable');
      }

      // add entry click handler if specified
      if (this.entryClickHandler) {
        var self = this;
        $(this.el).click({self: this}, this.entryClickHandler);
      }

      // add name click handler if specified
      if (this.nameClickHandler) {
        var self = this;
        $(this.el).children('.backbone-file-explorer-directory_entry_name').click(function() {
          self.nameClickHandler({
            self: self,
            path: self.model.path(),
            type: self.model.type()
          });
        });
      }

      // add action handlers
      if (this.actionHandlers) {
        for(var index in this.actionHandlers) {
          var handler = this.actionHandlers[index];
          var actionEl = $("<a class='actionHandler' href='#'>" + handler.iconHtml + "</a>")
            , self = this;
          // use closure to isolate handler logic
          (function(handler) {
            actionEl.click(function() {
              handler.logic({
                self: self,
                path: self.model.path(),
                type: self.model.type()
              });
            });
          })(handler);
          $(this.el).children('.backbone-file-explorer-directory_entry_actions').append(actionEl);
        }
      }

      if (this.model.children == undefined) {
        // remove directory button class for file entries
        $(this.el)
          .children('.backbone-file-explorer-directory_icon_button')
          .removeClass('backbone-file-explorer-directory_icon_button');
      } else {
        // add click handler to directory icon
        var self = this;
        $(this.el).children('.backbone-file-explorer-directory_icon_button').click(function() {
          self.toggleDirectory($(self.el));
        });
      }

      return this;
    }
  });

  /**
   * Backbone view for a subtree of files or directory entries.
   * @constructor
   */
  exports.DirectoryView = Backbone.View.extend({

    tagName: 'div',

    initialize: function() {
      this.cssIdNamespace     = this.options.cssIdNamespace;
        // allow overriding of container's ID to allow the same directory tree
        // to be shown in multiple contexts without CSS ID repeating

      this.model              = this.options.directory;
      this.explorer           = this.options.explorer;
      this.ajaxChildDataUrl   = this.options.ajaxChildDataUrl;
      this.itemsPerPage       = this.options.itemsPerPage;
      this.levelTemplate      = _.template(this.options.levelTemplate);
      this.entryTemplate      = _.template(this.options.entryTemplate);
      this.closeDirsByDefault = this.options.closeDirsByDefault;
      this.entryDisplayFilter = this.options.entryDisplayFilter;
      this.entryClickHandler  = this.options.entryClickHandler;
      this.nameClickHandler   = this.options.nameClickHandler;
      this.actionHandlers     = this.options.actionHandlers;
       // TODO: make this configurable
      this.pagingRenderFunctions = DEFAULT_PAGING_CONTROL_RENDER_FUNCTIONS;
   },

    // activate highlighting via adding/removing a CSS class
    activateHover: function(el) {
      $(el).hover(
        function() {
          $(this).addClass('backbone-file-explorer-entry-highlighted');
        },
        function() {
          $(this).removeClass('backbone-file-explorer-entry-highlighted');
        }
      );
    },

    // render links for navigating between pages of directory children
    renderPagingLinks: function(entry, levelEl, level, index, indexStart, previousOnly, previousIndexStarts) {
      var self = this;
      var $pagingEl = $('<div class="backbone-file-explorer-paging-link"></div>');

      // add link to previous entries, if any
      if (indexStart > 0) {
        var $prevEl = self.pagingRenderFunctions.previous(self.itemsPerPage);
        (function(index) {
          $prevEl.click(function() {
            $(levelEl).html('');
            $pagingEl.remove();
            self.renderChildren(self, entry, levelEl, level, previousIndexStarts.pop(), previousIndexStarts);
            $(levelEl).show();
          });
        })(index);
        $pagingEl.append($prevEl);
        if (!previousOnly) {
          $pagingEl.append(self.pagingRenderFunctions.separator());
        }
      }

      // add link to next entries, if any
      if (!previousOnly) {
        var $nextEl = self.pagingRenderFunctions.next(self.itemsPerPage);
        (function(index) {
          $nextEl.click(function() {
            $(levelEl).html('');
            $pagingEl.remove();
            previousIndexStarts.push(indexStart);
            self.renderChildren(self, entry, levelEl, level, index, previousIndexStarts);
            $(levelEl).show();
          });
        })(index);
        $pagingEl.append($nextEl);
      }

      $(levelEl).append($pagingEl);
    },

    // recursively render directory children
    renderChildren: function (self, entry, levelEl, level, indexStart, previousIndexStarts) {
      if (typeof previousIndexStarts == 'undefined') {
        previousIndexStarts = [];
      }

      // if entry is a directory, render children to directory level
      if (entry.children != undefined) {
        var counter = 0,
            pagingDisplayed = false;

        if (indexStart == undefined) {
          indexStart = 0;
        }

        for (var index = indexStart; index < entry.children.length; index++) {
          var child = entry.children[index]
            , allowDisplay = true;

          if (self.entryDisplayFilter) {
            allowDisplay = self.entryDisplayFilter(child);
          }

          if (self.itemsPerPage && counter >= self.itemsPerPage) {
            allowDisplay = false;
            if (!pagingDisplayed) {
              self.renderPagingLinks(entry, levelEl, level, index, indexStart, false, previousIndexStarts);
              pagingDisplayed = true;
            }
          } else if(allowDisplay) {
            counter++;
          }

          // if display is allowed, do
          if (allowDisplay) {
            // render entry
            var entryView = new exports.EntryView({
              cssIdNamespace: self.cssIdNamespace,
              container: self.explorer,
              entry: child,
              template: self.entryTemplate,
              entryClickHandler: self.entryClickHandler,
              nameClickHandler: self.nameClickHandler,
              actionHandlers: self.actionHandlers
            });

            // take note of file paths that correspond to CSS IDs
            // so they can be referenced by any external logic
            exports.Data.idPaths[entryView.cssId()] = child.displaypath();

            var entryEl = entryView.render().el
              , isOpenDir = false;

            // open the directory if the file explorer has been invoked with this directory
            // expressly open
            if (this.explorer.openDirs && this.explorer.openDirs.indexOf(entryView.cssId()) != -1) {
              isOpenDir = true;
            }

            // open the directory if the last snapshot had it open
            if (this.explorer.opened && this.explorer.opened.indexOf(entryView.cssId()) != -1) {
              isOpenDir = true;
            }

            // open directory, if applicable
            if ((child.children != undefined && !self.closeDirsByDefault) || isOpenDir) {
              $(entryEl).addClass('backbone-file-explorer-directory_open');
            }

            // set up hovering
            self.activateHover(entryEl);

            // add entry to current directory level
            $(levelEl).append(entryEl);

            // render child directories
            self.renderDirectoryLevel(levelEl, child, level + 1, isOpenDir);

            // work around issue with certain edge-case
            if (
              self.closeDirsByDefault
              && child.children != undefined
              && child.children.length == 0
            ) {
              $(entryEl).next().hide();
            }
          }
        }

        if (indexStart > 0 && !pagingDisplayed) {
          self.renderPagingLinks(entry, levelEl, level, index, indexStart, true, previousIndexStarts);
        }
      }
    },

    // render a single directory level then recurse through its children
    renderDirectoryLevel: function(destEl, entry, level, isOpen) {
      var level = level || 1
        , levelEl = $(this.levelTemplate());

      if (isOpen == undefined) {
        isOpen = false;
      }

      $(destEl).append(levelEl);

      // if not the top-level directory and everything's closed by default, then
      // hide this directory level
      if (level > 1 && this.closeDirsByDefault && !isOpen) {
        $(destEl).hide();
      }

      // if directories are closed by default, be lazy and only load child
      // entries when user hovers over entry, indicating they might open it
      if (this.closeDirsByDefault) {
        var self = this
          , rendered = false;

        // logic to do AJAX load of directory children, if applicable, and 
        // post-render UI styling (zebra striping, etc.)
        var uiUpdateLogic = function() {
          if (!rendered) {
            if (self.ajaxChildDataUrl && entry.type() == 'directory') {
              $.ajax({
                url: self.ajaxChildDataUrl,
                data: {
                  path: entry.path()
                },
                success: function(results) {
                  for(var index in results.entries) {
                    var entryName = results.entries[index],
                        entryProperties,
                        entryOptions = {'name': entryName};

                    // allow optional entry properties to be relayed (metadata, etc.)
                    if (typeof results.properties !== 'undefined') {
                      entryProperties = results.properties[entryName];
                      entryOptions['properties'] = entryProperties;
                    }

                    if (results.directories.indexOf(entryName) == -1) {
                      entry.addFile(entryOptions);
                    } else {
                      entry.addDir(entryOptions);
                    }
                  }

                  // this code repeats below and should be refactored
                  self.renderChildren(self, entry, levelEl, level);

                  // update zebra striping
                  $('.backbone-file-explorer-entry').removeClass(
                    'backbone-file-explorer-entry-odd'
                  );
                  $('.backbone-file-explorer-entry:visible:odd').addClass(
                    'backbone-file-explorer-entry-odd'
                  );

                  // re-bind drag/drop
                  if (self.explorer.moveHandler) {
                    self.explorer.initDragAndDrop();
                  }

                  // allow top level open state to be snapshotted
                  var entryCssId = self.explorer.id + '_' + entry.id();
                  if (self.explorer.opened && (self.explorer.opened.indexOf(entryCssId) != -1)) {
                    $(levelEl).show();
                  }
                }
              });
            } else {
              self.renderChildren(self, entry, levelEl, level);

              // update zebra striping
              $('.backbone-file-explorer-entry').removeClass(
                'backbone-file-explorer-entry-odd'
              );
              $('.backbone-file-explorer-entry:visible:odd').addClass(
                'backbone-file-explorer-entry-odd'
              );

              // re-bind drag/drop
              if (self.explorer.moveHandler) {
                self.explorer.initDragAndDrop();
              }
            }
            rendered = true;
          }
        };

        // if the directory is already open, trigger UI updating...
        // otherwise, wait for using to hover over the directory
        // to trigger it
        if (isOpen) {
          uiUpdateLogic();
          $(levelEl).show();
        } else {
          $(destEl).hover(uiUpdateLogic);
        }
      } else {
        // directories are open by default, so no lazy loading
        this.renderChildren(this, entry, levelEl, level);
      }
    },

    // render a group of files and directories
    render: function() {

      var entryView = new exports.EntryView({
        cssIdNamespace: this.cssIdNamespace,
        container: this.explorer,
        entry: this.model,
        template: this.entryTemplate
      });

      var entryEl = entryView.render().el;

      exports.Data.idPaths[entryView.cssId()] = entryView.model.displaypath();

      if (!this.closeDirsByDefault) {
        $(entryEl).addClass('backbone-file-explorer-directory_open');
      }

      this.activateHover(entryEl);

      $(this.el)
        .empty()
        .append(entryEl);

      var isOpen;

      // allow top level open state to be snapshotted
      if (this.explorer.opened && (this.explorer.opened.indexOf(entryView.cssId()) != -1)) {
        isOpen = true;
      } else {
        isOpen = false;
      }

      this.renderDirectoryLevel(this.el, this.model, 0, isOpen);

      return this;
    }
  });

  /**
   * Logic to handle keeping track of the location of a dragged entry.
   * @function
   */
  function dragHandler(event, ui) {
    var id = event.target.id;

    // if an element hasn't been dragged yet, take note of its start
    // position
    if (exports.Data.startY[id] == undefined) {
     exports.Data.startX[id] = event.target.offsetLeft;
     exports.Data.startY[id] = event.target.offsetTop;
    }

    // reposition the element
    ui.position = {
      'top': exports.Data['mouseY'] - exports.Data.startY[id] + 5,
      'left': exports.Data['mouseX'] - exports.Data.startX[id] + 5
    };
  };

  /**
   * Backbone view for a list of files/directories.
   * @constructor
   */
  exports.EntryList = Backbone.View.extend({

    tagName: 'div',

    initialize: function() {
      this.entries               = this.options.entries || [];
      this.moveHandler           = this.options.moveHandler;
      this.id                    = $(this.el).attr('id');
      this.levelTemplate         = this.options.levelTemplate;
      this.entryTemplate         = this.options.entryTemplate;
      // TODO: make this configurable
      this.pagingRenderFunctions = DEFAULT_PAGING_CONTROL_RENDER_FUNCTIONS;
      this.itemsPerPage          = this.options.itemsPerPage;
      this.currentPage           = 0;

      this.render();
      this.initDragAndDrop();
    },

    dragHandler: dragHandler,

    // bind/re-bind drag-and-drop logic
    initDragAndDrop: function() {
      if (this.moveHandler) {
        // bind drag-and-drop functionality
        var self = this;

        // bind all list entries to drag handler
        $(this.el).find('.backbone-file-explorer-entry:not(:first):not(.not_draggable)').draggable({
          stack: 'div',
          drag: function(event, ui) {
            event.data = { self: self };
            self.dragHandler(event, ui);
          },
          revert: function(event, ui) {
            return !event;
          }
        });
      }
    },

    // render the entry list
    render: function() {
      $(this.el).empty();

      // intialize paging-related variables
      if (this.itemsPerPage) {
        var startItem = this.currentPage * this.itemsPerPage;
        var endItem = startItem + this.itemsPerPage;
      }

      // render each entry in the list
      for (var index = 0; index < this.entries.length; index++) {
        var allowDisplay = true;

        // if paging is enabled, determine whether entry is on current
        // page and should be displayed
        if (this.itemsPerPage) {
          if (index >= startItem && index < endItem) {
            allowDisplay = true;
          } else {
            allowDisplay = false;
          }
        }

        if (allowDisplay) {
          if (this.entries[index].type() == 'directory') {
            var directoryViewOptions = {
              cssIdNamespace: this.id + '_' + index,
                // provide CSS ID namespace as same directory might be shown
                // more than once
              explorer: this,
              directory: this.entries[index],
              levelTemplate: this.levelTemplate,
              entryTemplate: this.entryTemplate,
              closeDirsByDefault: true,
              //entryClickHandler: this.options.entryClickHandler,
              //nameClickHandler: this.options.nameClickHandler,
              //actionHandlers: this.options.actionHandlers
            };

            // if paging is enabled, pass on to directory view
            if (this.itemsPerPage) {
              directoryViewOptions.itemsPerPage = this.itemsPerPage;
            }

            var entry = new exports.DirectoryView(directoryViewOptions);
          } else {
            var entry = new exports.EntryView({
              el: this.el,
              entry: this.entries[index],
              template: _.template(this.entryTemplate),
              container: this
            });
          }

          // take note of entry's path
          exports.Data.idPaths[this.id + '_' + entry.model.id()] = entry.model.displaypath();
          entry.render();

          // add rendered entry to the view's DOM element
          $(this.el).append(entry.el);
        }
      }

      if (this.itemsPerPage) {
        var self = this;

        // render previous page control, if applicable
        if (startItem > 0) {
          var $prevEl = this.pagingRenderFunctions.previous(this.itemsPerPage);
          $prevEl.click(function() {
            self.currentPage -= 1;
            self.render();
            self.initDragAndDrop();
          });
          $(this.el).append($prevEl);
        }

        // render next control, if applicable
        if (this.entries.length > (startItem + this.itemsPerPage)) {
          if (startItem > 0) {
            $(this.el).append(this.pagingRenderFunctions.separator());
          }
          var $nextEl = this.pagingRenderFunctions.next(this.itemsPerPage);
          $nextEl.click(function() {
            self.currentPage += 1;
            self.render();
            self.initDragAndDrop();
          });
          $(this.el).append($nextEl);
        }
      }

      return this;
    }
  });

  /**
   * Backbone view for a file explorer.
   * @constructor
   */
  exports.FileExplorer = Backbone.View.extend({

    tagName: 'div',

    initialize: function() {
      this.ajaxChildDataUrl = this.options.ajaxChildDataUrl;
      this.directory        = this.options.directory;
      this.structure        = this.options.structure;
      this.itemsPerPage     = this.options.itemsPerPage || false;
      this.moveHandler      = this.options.moveHandler;
      this.openDirs         = this.options.openDirs;
      this.openDirs         = this.openDirs || [];
      this.id               = $(this.el).attr('id');
      this.render();
      this.initDragAndDrop();
    },

    // bind/re-bind drag-and-drop logic
    initDragAndDrop: function() {
      if (this.moveHandler) {
        // bind drag-and-drop functionality
        var self = this;
        var $el = $(this.el);

        // exclude top-level directory from being dragged
        // Don't bind drag to anything with 'not_draggable' class
        $el.find('.backbone-file-explorer-entry:not(:first):not(.not_draggable)').draggable({
          stack: 'div',
          drag: function(event, ui) {
            event.data = { self: self };
            self.dragHandler(event, ui);
          },
          revert: function(event, ui) {
            return !event;
          }
        });

        if ($el.attr('id') !== 'originals') {
          $el.find('.backbone-file-explorer-entry').droppable({
            drop: function(event, ui) {
              event.data = { self: self };
              self.dropHandler(event, ui);
            }
          });
        }
      }
    },

    // find an entry corresponding to a given path
    getByPath: function(path) {
      var found = this.findEntry(function(entry) {
        if (typeof entry != 'undefined') {
          return entry.displaypath() == path;
        } else {
          return false;
        }
      });
      if (found.length > 0) {
        return found[0];
      }
    },

    // find entry object
    findEntry: function(testLogic, found, entry) {
      // initialize result set
      if (typeof found === 'undefined') {
        found = [];
      }

      // default to root entry
      if (typeof entry === 'undefined') {
        entry = this.dirView.model;
      } else {
        // add entry to results if the test passes
        if (testLogic(entry)) {
          found.push(entry);
        }
      }

      // find in entry children
      var foundEntry = false;
      if (typeof entry.children != 'undefined') {
        for (var index = 0; index < entry.children.length; index++) {
          this.findEntry(testLogic, found, entry.children[index]);
        }
      }

      return found;
    },

    // convert JSON structure to entry objects
    structureToObjects: function(structure, base) {
      if (structure.children != undefined) {
        base.set({name: structure.name});
        if (structure.parent != undefined) {
          base.set({parent: structure.parent});
        }
        for (var index in structure.children) {
          var child = structure.children[index];
          if (child.children != undefined) {
            var parent = base.addDir({name: child.name, properties: child.properties});
            parent = this.structureToObjects(child, parent);
          } else {
            base.addFile({name: child.name, properties: child.properties});
          }
        }
      } else {
        base.addFile(structure.name);
      }

      // allow structure to provide additional data for special applications
      if (typeof structure.data != 'undefined') {
        base.set({'data': structure.data});
      }

      return base;
    },

    // indicate, in the UI, that a background task is happening
    busy: function() {
      $(this.el).append('<span id="backbone-file-explorer-busy-text">Loading...</span>');
      $(this.el).addClass('backbone-file-explorer-busy');
      $(this.el).removeClass('backbone-file-explorer-idle');
    },

    // indicate, in the UI, that no background task is happening
    idle: function() {
      $('#backbone-file-explorer-busy-text').remove();
      $(this.el).addClass('backbone-file-explorer-idle');
      $(this.el).removeClass('backbone-file-explorer-busy');
    },

    // take note of which folders have been opened
    snapShotOpenedFolders: function() {
      this.opened = [];
      var self = this;
      $(this.el).find('.backbone-file-explorer-directory').each(function(index, value) {
        if($(value).hasClass('backbone-file-explorer-directory_open')) {
            self.opened.push($(value).attr('id'));
        }
      }); 
    },

    // restore opened folders to the previous snapshot
    restoreOpenedFolders: function() {
      for (var index in this.opened) {
        var cssId = this.opened[index],
            $openEl = $('#' + cssId);
        this.openFolder($openEl);
      }
    },

    openFolder: function ($openEl) {
      $openEl.next().show();
      if (!$openEl.hasClass('backbone-file-explorer-directory_open')) {
        $openEl.addClass('backbone-file-explorer-directory_open');
      }
    },

    // logic to keep track of where a dragged directory entry is
    dragHandler: dragHandler,

    // logic to keep handle dropping a directory entry
    dropHandler: function(event, ui) {
      var droppedId = $(ui.draggable).attr('id');
      var containerId = event.target.id;
      var self = event.data.self;

      if (droppedId != containerId) {
        var droppedPath = exports.Data.idPaths[droppedId];
        var containerPath = exports.Data.idPaths[containerId];
        var moveAllowed = containerPath.indexOf(droppedPath) != 0;
        self.moveHandler({
          'self': self,
          'droppedPath': droppedPath,
          'containerPath': containerPath,
          'allowed': moveAllowed
        });
      }
    },

    // use a directory entry's CSS ID to determine its filepath
    getPathForCssId: function(id) {
      return exports.Data.idPaths[id];
    },

    // use a directory entry's CSS ID to determine whether it's a file or dir
    getTypeForCssId: function(id) {
      if ($('#' + id).hasClass('backbone-file-explorer-directory')) {
        return 'directory';
      } else {
        return 'file';
      }
    },

    // render the file explorer
    render: function() {
      var directory = this.directory;

      // if a JSON directory structure has been provided, render it
      // into entry objects
      if(this.structure) {
        directory = this.structureToObjects(
          this.structure,
          new exports.Directory
        );
      }

      this.snapShotOpenedFolders();

      this.dirView = new exports.DirectoryView({
        explorer: this,
        ajaxChildDataUrl: this.ajaxChildDataUrl,
        directory: directory,
        openDirs: this.openDirs,
        itemsPerPage: this.itemsPerPage,
        levelTemplate: this.options.levelTemplate,
        entryTemplate: this.options.entryTemplate,
        closeDirsByDefault: this.options.closeDirsByDefault,
        entryDisplayFilter: this.options.entryDisplayFilter,
        entryClickHandler: this.options.entryClickHandler,
        nameClickHandler: this.options.nameClickHandler,
        actionHandlers: this.options.actionHandlers
      });

      $(this.el)
        .empty()
        .append(this.dirView.render().el);

      this.restoreOpenedFolders();

      $('.backbone-file-explorer-entry:odd').addClass('backbone-file-explorer-entry-odd');

      return this;
    }
  });
})(typeof exports === 'undefined' ? this['fileBrowser'] = {} : exports);
