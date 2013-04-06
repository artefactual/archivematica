(function(exports) {

  // patch in indexOf for IE8
  // As per: http://stackoverflow.com/questions/3629183/why-doesnt-indexof-work-on-an-array-ie8
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

  exports.Data = {
    idPaths: {},
    startX: {},
    startY: {}
  };

  exports.File = Backbone.Model.extend({

    // generate id without slashes and replacing periods
    id: function() {
      return this.path().replace(/\//g, '_').replace('.', '__');
    },

    path: function() {
      return this.get('parent') + '/' + this.get('name');
    },

    type: function() {
      return (this.children == undefined) ? 'file' : 'directory';
    }
  });

  exports.Directory = exports.File.extend({
    initialize: function() {
      this.children = [];
      this.cssClass = 'backbone-file-explorer-directory';
    },

    addChild: function(options, Type) {
      var child = new Type(options)
        , parent = this.get('parent');

      parent = (parent != undefined)
        ? parent + '/' + this.get('name')
        : this.get('name');

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

  exports.EntryView = Backbone.View.extend({

    initialize: function() {
      this.model     = this.options.entry;
      this.explorer  = this.options.explorer;
      this.className = (this.model.children != undefined)
        ? 'backbone-file-explorer-directory'
        : 'directory-file';
      this.template          = this.options.template;
      this.entryClickHandler = this.options.entryClickHandler;
      this.nameClickHandler  = this.options.nameClickHandler;
      this.actionHandlers    = this.options.actionHandlers;
    },

    context: function() {
      var context = this.model.toJSON();
      context.className = this.className;
      return context;
    },

    cssId: function() {
      return this.explorer.id + '_' + this.model.id();
    },

    render: function() {
      var context = this.context()
        , html = this.template(context);

      this.el = $(html);
      $(this.el).addClass(this.className);

      // set CSS ID for entries (used to capture whether directory is
      // open/closed by user between data refreshes, etc.)
      var id = (this.explorer) ? this.explorer.id + '_' : '';
      $(this.el).attr('id', id + this.model.id());

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
        $(this.el).children('.backbone-file-explorer-directory_icon_button').removeClass('backbone-file-explorer-directory_icon_button');
      } else {
        // add click handler to directory icon
        var self = this;
        $(this.el).children('.backbone-file-explorer-directory_icon_button').click(function() {
          self.explorer.toggleDirectory($(self.el));
        });
      }

      return this;
    }
  });

  exports.DirectoryView = Backbone.View.extend({

    tagName: 'div',

    initialize: function() {
      this.model              = this.options.directory;
      this.explorer           = this.options.explorer;
      this.ajaxChildDataUrl   = this.options.ajaxChildDataUrl;
      this.levelTemplate      = _.template(this.options.levelTemplate);
      this.entryTemplate      = _.template(this.options.entryTemplate);
      this.closeDirsByDefault = this.options.closeDirsByDefault;
      this.entryDisplayFilter = this.options.entryDisplayFilter;
      this.entryClickHandler  = this.options.entryClickHandler;
      this.nameClickHandler   = this.options.nameClickHandler;
      this.actionHandlers     = this.options.actionHandlers;
    },

    activateHover: function(el) {
      console.log('activate');
      $(el).hover(
        function() {
          $(this).addClass('backbone-file-exporer-entry-highlighted');
        },
        function() {
          $(this).removeClass('backbone-file-exporer-entry-highlighted');
        }
      );
    },

    renderChildren: function (self, entry, levelEl, level) {
      // if entry is a directory, render children to directory level
      if (entry.children != undefined) {

        for (var index in entry.children) {
          var child = entry.children[index]
            , allowDisplay = true;

          if (self.entryDisplayFilter) {
            allowDisplay = self.entryDisplayFilter(child);
          }

          // if display is allowed, do
          if (allowDisplay) {
            // take note of file paths that correspond to CSS IDs
            // so they can be referenced by any external logic
            var id = (this.explorer) ? this.explorer.id + '_' : '';
            id = id + child.id();
            exports.Data.idPaths[id] = child.path();

            // render entry
            var entryView = new exports.EntryView({
              explorer: self.explorer,
              entry: child,
              template: self.entryTemplate,
              entryClickHandler: self.entryClickHandler,
              nameClickHandler: self.nameClickHandler,
              actionHandlers: self.actionHandlers
            });

            var entryEl = entryView.render().el
              , isOpenDir = false;

            if (this.explorer.openDirs && this.explorer.openDirs.indexOf(entryView.cssId()) != -1) {
              isOpenDir = true;
            }

            // open directory, if applicable
            if ((child.children != undefined && !self.closeDirsByDefault) || isOpenDir) {
              $(entryEl).addClass('backbone-file-explorer-directory_open');
            }

            // set up hovering
            self.activateHover(entryEl);

            // add entry to current directory livel
            $(levelEl).append(entryEl);

            // render child directories
            self.renderDirectoryLevel(levelEl, child, level + 1, isOpenDir);

            // work around issue with certain edge-case
            if (
              self.closeDirsByDefault
              && child.children != undefined
              && (child.children.length == 0 || !allowDisplay)
            ) {
              $(entryEl).next().hide();
            }
          }
        }
      }
    },

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

        var uiUpdateLogic = function() {
          if (!rendered) {
            if (self.ajaxChildDataUrl && entry.type() == 'directory') {
              $.ajax({
                url: self.ajaxChildDataUrl,
                data: {
                  path: entry.path()
                },
                success: function(results) {
                  //console.log(results);
                  for(var index in results.entries) {
                    var entryName = results.entries[index];
                    if (results.directories.indexOf(entryName) == -1) {
                      entry.addFile({name: entryName});
                    } else {
                      entry.addDir({name: entryName});
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

        if (isOpen) {
          uiUpdateLogic();
          $(levelEl).show();
        } else {
          $(destEl).hover(uiUpdateLogic);
        }
      } else {
        this.renderChildren(this, entry, levelEl, level);
      }
    },

    render: function() {
      var entryView = new exports.EntryView({
        explorer: this.explorer,
        entry: this.model,
        template: this.entryTemplate
      });

      var entryEl = entryView.render().el;

      exports.Data.idPaths[entryView.cssId()] = entryView.model.path();

      if (!this.closeDirsByDefault) {
        $(entryEl).addClass('backbone-file-explorer-directory_open');
      }

      this.activateHover(entryEl);

      $(this.el)
        .empty()
        .append(entryEl);

      this.renderDirectoryLevel(this.el, this.model);

      return this;
    }
  });

  exports.FileExplorer = Backbone.View.extend({

    tagName: 'div',

    initialize: function() {
      this.ajaxChildDataUrl = this.options.ajaxChildDataUrl;
      this.directory        = this.options.directory;
      this.structure        = this.options.structure;
      this.moveHandler      = this.options.moveHandler;
      this.openDirs         = this.options.openDirs;
      this.openDirs         = this.openDirs || [];
      this.id               = $(this.el).attr('id');
      this.render();
      this.initDragAndDrop();
    },

    initDragAndDrop: function() {
      if (this.moveHandler) {
        // bind drag-and-drop functionality
        var self = this;

       // exclude top-level directory from being dragged
       $(this.el)
          .find('.backbone-file-explorer-entry:not(:first)')
          .unbind('drag')
          .bind('drag', {'self': self}, self.dragHandler);

       // allow top-level directory to be dragged into
       $(this.el)
          .find('.backbone-file-explorer-entry')
          .unbind('drop')
          .bind('drop', {'self': self}, self.dropHandler);
      }
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
            var parent = base.addDir({name: child.name});
            parent = this.structureToObjects(child, parent);
          } else {
            base.addFile({name: child.name});
          }
        }
      } else {
        base.addFile(structure.name);
      }

      return base;
    },

    busy: function() {
      $(this.el).append('<span id="backbone-file-explorer-busy-text">Loading...</span>');
      $(this.el).addClass('backbone-file-explorer-busy');
      $(this.el).removeClass('backbone-file-explorer-idle');
    },

    idle: function() {
      $('#backbone-file-explorer-busy-text').remove();
      $(this.el).addClass('backbone-file-explorer-idle');
      $(this.el).removeClass('backbone-file-explorer-busy');
    },

    snapShotToggledFolders: function() {
      this.toggled = [];
      var self = this;
      $('.backbone-file-explorer-directory').each(function(index, value) {
        if (!$(value).next().is(':visible')) {
          self.toggled.push($(value).attr('id'));
        }
      }); 
    },

    restoreToggledFolders: function() {
      for (var index in this.toggled) {
        var cssId = this.toggled[index];
        this.toggleDirectory($('#' + cssId));
      }
    },

    dragHandler: function(event) {
      var id = event.currentTarget.id
        , $el = $('#' + event.currentTarget.id)
        , offsets = $el.offset();

      if (exports.Data.startY[id] == undefined) {
       exports.Data.startX[id] = offsets.left;
       exports.Data.startY[id] = offsets.top;
      }

      $el.css({'z-index': 1});
      $el.css({left: event.offsetX - exports.Data.startX[id]});
      $el.css({top: event.offsetY - exports.Data.startY[id]});
    },

    dropHandler: function(event) {
      var droppedId   = event.dragTarget.id;
      var containerId = event.dropTarget.id;
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
      $('#' + droppedId).css({left: 0});
      $('#' + droppedId).css({top: 0});
    },

    toggleDirectory: function($el) {
      $el.next().toggle();
      if ($el.next().is(':visible')) {
        $el.addClass('backbone-file-explorer-directory_open');
      } else {
        $el.removeClass('backbone-file-explorer-directory_open');
      }
    },

    getPathForCssId: function(id) {
      return exports.Data.idPaths[id];
    },

    getTypeForCssId: function(id) {
      if ($('#' + id).hasClass('backbone-file-explorer-directory')) {
        return 'directory';
      } else {
        return 'file';
      }
    },

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

      var toggledFolders = this.snapShotToggledFolders();

      this.dirView = new exports.DirectoryView({
        explorer: this,
        ajaxChildDataUrl: this.ajaxChildDataUrl,
        directory: directory,
        openDirs: this.openDirs,
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

      this.restoreToggledFolders();

      $('.backbone-file-explorer-entry:odd').addClass('backbone-file-explorer-entry-odd');

      return this;
    }
  });
})(typeof exports === 'undefined' ? this['fileBrowser'] = {} : exports);
