import angular from 'angular';
import moment from 'moment';
import '../vendor/angular-ui-bootstrap/ui-bootstrap-custom-tpls-0.14.3.min.js';

angular.module('archivesSpaceController', ['alertService', 'sipArrangeService', 'transferService', 'ui.bootstrap']).

// This controller does a lot. Functions handled by this controller and its partial include:
// * Fetching data from ArchivesSpace to feed to the tree view in the partial.
// * Creating new ArchivesSpace records, and editing existing records
// * Creating new digital object components, and editing existing components
// * SIP arrange interactions with the contents of digital object components
//
// The tree displayed in the partial has three types of objects:
// * ArchivesSpace records
// * digital object components
// * SIP arrange files/directories
// These are distinguished via the "type" parameter, which has the following values:
// * resource (ArchivesSpace resource record)
// * resource_component (ArchivesSpace archival object record)
// * arrange_entry (SIP arrange file or directory)
// * digital_object (digital object component)
//
// These share several key properties, such as "title", some other values differ.
// Both the partials and some parts of code in the controller distinguish between these
// categories using the "type" parameter, and use that to control display logic and to
// dispatch to different functions which operate on them.
controller('ArchivesSpaceController', ['$scope', 'gettextCatalog', '$uibModal', 'Alert', 'ArchivesSpace', 'SipArrange', 'Transfer', function($scope, gettextCatalog, $uibModal, Alert, ArchivesSpace, SipArrange, Transfer) {
  $scope.get_rights_url = (record) => {
    if (record === undefined) {
      return '';
    }
    if (record.type !== 'resource' && record.type !== 'resource_component') {
      return '';
    }
    return `/access/archivesspace/${record.id.replace(/\//g, '-')}/rights/`;
  };

  // Reformats several properties on the form object, returning them in
  // a format suitable for use with the ArchivesSpace service's `edit`
  // and `add_child` functions.
  // Returns a modified copy of the passed-in object.
  var reformat_form_results = form => {
    var copy = Object.assign({}, form);
    copy.notes = [];
    copy.levelOfDescription = form.level;

    // If the notes are disabled (the record has existing notes),
    // send empty array to avoid overwriting them, otherwise build
    // notes array and delete note fields
    if (!form.disableNotesEdit) {
      if (copy.note) {
        copy.notes.push({
          type: 'odd',
          content: copy.note,
        });
      }
      if (copy.accessrestrict_note) {
        copy.notes.push({
          type: 'accessrestrict',
          content: copy.accessrestrict_note,
        });
      }
    }

    delete copy.note;
    delete copy.accessrestrict_note;

    if (form.date_expression) {
      copy.dates = form.date_expression;
    } else if (form.start_date) {
      copy.dates = copy.start_date;
      if (form.end_date) {
        copy.dates += ' - ' + copy.end_date;
      }
    }

    return copy;
  };

  var append_child = (node, child) => {
    if (!node.has_children) {
      node.has_children = true;
      node.children = [];
      node.children_fetched = false;
    }
    node.children.push(child);
  };

  var levels_of_description = ArchivesSpace.get_levels_of_description().$object;

  // Opens a modal to edit an ArchivesSpace record.
  $scope.edit = node => {
    if (node.type !== 'resource' && node.type !== 'resource_component') {
      return;
    }

    var form = $uibModal.open({
      templateUrl: 'archivesspace/form.html',
      controller: 'ArchivesSpaceEditController',
      controllerAs: 'form',
      resolve: {
        levels: () => {
          return levels_of_description;
        },
        title: () => {
          return node.title;
        },
        level: () => {
          return node.levelOfDescription;
        },
        start_date: () => {
          return false;
        },
        end_date: () => {
          return false;
        },
        date_expression: () => {
          return false;
        },
        notes: () => {
          return node.notes;
        }
      },
    });
    form.result.then(result => {
      // Assign these to variables so we can restore them if the PUT fails
      var original_title = node.title;
      var original_level = node.levelOfDescription;
      var original_note = node.notes;

      node.title = result.title;
      var formatted = reformat_form_results(result);
      node.levelOfDescription = formatted.levelOfDescription;
      node.notes = formatted.notes;
      node.dates = formatted.dates;
      // Any node with pending requests will be marked as non-editable
      node.request_pending = true;

      var on_success = response => {
        if (result.disableNotesEdit) {
          // Restore notes after request when notes edit
          // is disabled and an empty array has been sent
          node.notes = original_note;
        }
        node.request_pending = false;
      };

      var on_failure = error => {
        // Restore the original title/level since the request failed
        node.title = original_title;
        node.levelOfDescription = original_level;
        node.notes = original_note;
        node.request_pending = false;

        var title = node.title;
        if (node.identifier) {
          title = `${title} (${node.identifier})`;
        }

        Alert.alerts.push({
          type: 'danger',
          message: gettextCatalog.getString('Unable to submit edits to record "{{title}}"; check dashboard logs.', { title: title }),
        });
      };

      // Only post the information that may have changed for this node.
      // Otherwise, this runs into problems with cyclic references and including
      // irrelevant information that hasn't changed but also hasn't been
      // populated correctly.
      let node_to_post = {
        'id': node.id,
        'title': node.title,
        'level': node.levelOfDescription,
        'notes': node.notes,
      };

      ArchivesSpace.edit(node.id, node_to_post).then(on_success, on_failure);
    });
  };

  // Opens a modal to add a new ArchivesSpace record.
  // This is slightly different from the "edit" form above,
  // since there are a few fields that are read-only.
  $scope.add_child = function(node) {
    var form = $uibModal.open({
      templateUrl: 'archivesspace/form.html',
      controller: 'ArchivesSpaceEditController',
      controllerAs: 'form',
      resolve: {
        levels: () => {
          return ArchivesSpace.get_levels_of_description().$object;
        },
        title: () => {
          return '';
        },
        level: () => {
          return '';
        },
        start_date: () => {
          return '';
        },
        end_date: () => {
          return '';
        },
        date_expression: () => {
          return '';
        },
        notes: () => {
          return [];
        }
      },
    });
    form.result.then(result => {
      var result = reformat_form_results(result);

      var on_success = response => {
        result.id = response.id;
        result.parent = node;
        result.type = 'resource_component';
        result.display_title = result.title;
        if (result.dates) {
          if (result.title) {
            result.display_title += ', ';
          }
          result.display_title += result.dates;
        }
        append_child(node, result);
      };

      var on_failure = error => {
        Alert.alerts.push({
          type: 'danger',
          message: gettextCatalog.getString('Unable to add new child record to record {{id}}', { id: node.id }),
        });
      };

      ArchivesSpace.add_child(node.id, result).then(on_success, on_failure);
    });
  };

  // Add a "digital object component" object, to which files can be dragged
  $scope.add_digital_object = node => {
    var result = {
      title: 'Digital Object',
      resourceid: node.id,
      type: 'digital_object'
    };

    var on_success = response => {
      result.id = response.component_id;
      result.path = response.component_path;
      append_child(node, result);
      if ($scope.expanded_nodes.indexOf(node) === -1) {
        $scope.expanded_nodes.push(node);
        // Expanded event will not fire if the node was programmatically expanded - this loads children
        $scope.on_toggle(node, true);
      } else {
        // Reload the directory to reflect new contents
        load_element_children(node);
      }
    };

    var on_failure = result => {
      Alert.alerts.push({
        type: 'danger',
        message: gettextCatalog.getString('Unable to add new digital object component to record {{id}}', { id: node.id }),
      });
    };

    ArchivesSpace.create_digital_object_component(node.id, result).then(on_success, on_failure);
  };

  // tree options used by angular-tree-view
  $scope.options = {
    dirSelectable: true,
    equality: (a, b) => {
      if (a === undefined || b === undefined) {
        return false;
      } else if (a.id && b.id) {
        return a.id === b.id;
      } else {
        return a.path === b.path;
      }
    },
    isLeaf: node => {
      return !node.has_children && node.type !== 'digital_object';
    },
  };

  // Loads the children of the specified element,
  // along with arranged SIP contents that might exist
  var load_element_children = node => {
    $scope.loading = true;

    var on_failure_aspace = error => {
      Alert.alerts.push({
        type: 'danger',
        message: gettextCatalog.getString('Unable to fetch record {{id}} from ArchivesSpace!', { id: node.id }),
      });
      $scope.loading = false;
    };

    var on_failure_arrange = error => {
      Alert.alerts.push({
        type: 'danger',
        message: gettextCatalog.getString('Unable to fetch record {{path}} from Arrangement!', { path: node.path }),
      });
      $scope.loading = false;
    };

    node.children = [];

    if (node.id && node.type !== 'digital_object') {  // ArchivesSpace node
      ArchivesSpace.get_children(node.id).then(children => {
        children.map(element => element.parent = node);
        node.children = node.children.concat(children);
        node.children_fetched = true;
        $scope.loading = false;
      }, on_failure_aspace);

      // Also check to see if there are any digital object components;
      // if so, render them like any other ASpace objects
      ArchivesSpace.digital_object_components(node.id).then(components => {
        node.children = node.children.concat(components);
      });
    } else {  // SipArrange node
      SipArrange.list_contents(node.path, node).then(entries => {
        node.children = entries;
        node.children_fetched = true;
        $scope.loading = false;
      }, on_failure_arrange);
    }
  };

  $scope.on_toggle = function(node, expanded) {
    if ((!expanded || !node.has_children || node.children_fetched) && node.type !== 'digital_object') {
      return;
    }

    load_element_children(node);
  };

  $scope.load_data = (query) => {
    let on_success = data => {
      $scope.data = data;
      $scope.loading = false;
    };
    let on_failure = response => {
      $scope.loading = false;
      Alert.alerts.push({
        type: 'danger',
        message: gettextCatalog.getString('Unable to access ArchivesSpace; check dashboard logs!'),
      });
    };

    $scope.loading = true;
    if (query === undefined) {
      return ArchivesSpace.all().then(on_success, on_failure);
    } else {
      return ArchivesSpace.search(query).then(on_success, on_failure);
    }
  };

  // Prevent a given file or its descendants from being dragged more than once
  var dragged_ids = [];
  var log_ids = file => {
    dragged_ids.push(file.id);
    if (file.children) {
      for (var i = 0; i < file.children.length; i++) {
        log_ids(file.children[i]);
      }
    }
  };

  // Filter the list of dragged files to contain only files with the "display"
  // parameter, so that only visibly selected files are dragged over
  var filter_files = file => {
    if (!file.display) {
      return {};
    }

    // Filter children recursively
    if (file.children) {
      var children = file.children;
      file.children = [];
      angular.forEach(children, child => {
        child = filter_files(child);
        // Omit empty objects, or directories whose children have all been filtered out
        if (child.id && child.type === 'file' || (child.children && child.children.length > 0)) {
          file.children.push(child);
        }
      });
    }

    return file;
  };

  // Called when a file is dragged from the transfer backlog onto an element,
  // or when a file is dragged from SIP arrange onto an element.
  // This dispatches to different functions depending on whether the source is
  // transfer backlog or SIP arrange, and whether the target is an ArchivesSpace
  // record or a SIP arrange directory (including ArchivesSpace records).
  $scope.drop = function(unused, ui) {
    if ($scope.loading) {
      return;
    }

    var type = ui.draggable.attr('file-type');
    var is_arrange_file = this.type !== 'digital_object';
    if (type === 'arrange') {
      var path = ui.draggable.attr('file-path');
      if (is_arrange_file) {
        return copy_arrange_to_arrange.apply(this, [path]);
      } else {
        return copy_arrange_to_aspace.apply(this, [path]);
      }
    } else {
      var file = Transfer.id_map[ui.draggable.attr('uuid')];
      if (is_arrange_file) {
        return copy_backlog_to_arrange.apply(this, [file]);
      } else {
        return copy_backlog_to_aspace.apply(this, [file]);
      }
    }
  };

  var copy_arrange_to_arrange = function(path) {
    var on_move = () => {
      load_element_children(this);
    };

    SipArrange.copy_to_arrange(path, '/arrange/' + this.path).then(on_move);
  };

  var copy_arrange_to_aspace = function(path) {
    var on_move = () => {
      load_element_children(this);
    };

    SipArrange.copy_to_arrange(path, this.path).then(on_move);
  };

  // TODO use SipArrange's copy
  var basename = path => path.replace(/\\/g, '/').replace( /.*\//, '' );

  // TODO use SipArrange's copy
  var generate_files_list = (file, source_path, destination_path) => {
    let paths = {'source': [], 'destination': []};

    if (!file.display) {
      return paths;
    }

    if (file.type === 'file') {
      paths.source.push(source_path + file.relative_path);
      paths.destination.push(destination_path + basename(file.relative_path));
    }

    if (file.children) {
      angular.forEach(file.children, child => {
        let child_paths = generate_files_list(child, source_path,
          destination_path + basename(file.relative_path) + '/');
        paths.source = paths.source.concat(child_paths.source);
        paths.destination = paths.destination.concat(child_paths.destination);
      });
    }
    return paths;
  };

  var copy_backlog_to_aspace = function(file) {
    // create a deep copy of the file and its children so we don't mutate
    // the copies used in the backlog
    file = filter_files(Object.assign({}, file));
    if (!file.id) {
      return;
    }

    var on_copy = () => {
      if ($scope.expanded_nodes.indexOf(this) === -1) {
        $scope.expanded_nodes.push(this);
        // expanded event will not fire if the node was programmatically expanded - this loads children
        $scope.on_toggle(this, true);
      } else {
        // Reload the directory to reflect new contents
        load_element_children(this);
      }
    };

    let paths = generate_files_list(file,
      '/originals/',
      this.path
    );

    // TODO make sure `path` property is correctly specified
    $scope.$apply(() => {
      $scope.loading = true;

      this.has_children = true;
      this.children = [];
      this.children_fetched = false;
      SipArrange.copy_to_arrange(paths.source, paths.destination).then(on_copy);
    });
  };

  var copy_backlog_to_arrange = function(file) {
    var source_path;
    if (file.type === 'file') {
      source_path = file.relative_path;
    } else {
      source_path = file.relative_path + '/';
    }

    // Reload the directory to reflect new contents
    var on_copy = () => {
      load_element_children(this);
    };

    $scope.$apply(() => {
      SipArrange.copy_to_arrange('/arrange/' + source_path, '/arrange/' + this.path).then(on_copy);
    });
  };

  // Deletes an ArchivesSpace record or a SIP arrange file/directory.
  $scope.remove = function(node) {
    if ($scope.loading) {
      return;
    }

    var on_delete = element => {
      // `node.parent` is undefined if this is a root-level directory
      var siblings = node.parent ? node.parent.children : $scope.data.children;
      var idx = siblings.indexOf(node);
      if (idx !== -1){
        siblings.splice(idx, 1);
      }
      $scope.selected = undefined;
    };

    // TODO is this a reliable way to tell nodes apart?
    if (node.id) { // ArchivesSpace node
      ArchivesSpace.remove(node.id).then(on_delete);
    } else {  // SipArrange node
      SipArrange.remove(node.path).then(on_delete);
    }
  };

  // Starts a SIP from an ArchivesSpace record.
  // This uses the digital object components attached to the ArchivesSpace record,
  // each of which will become a directory in the newly-created SIP.
  $scope.finalize_arrangement = function(node) {
    var on_success = () => {
      node.request_pending = false;
      Alert.alerts.push({
        type: 'success',
        message: gettextCatalog.getString('Successfully started SIP from record "{{title}}"', { title: node.display_title }),
      });

      // Remove the digital object components so the user doesn't try to add new items
      node.children = node.children.filter(element => element.type !== 'digital_object');
    };
    var on_failure = error => {
      node.request_pending = false;
      var message;
      // error.message won't be defined if this returned an HTML 500
      if (error.data.message && error.data.message.startsWith('No SIP Arrange')) {
        message = gettextCatalog.getString('Unable to start SIP; no files arranged into record "{{title}}".', { title: node.display_title });
      } else {
        message = gettextCatalog.getString('Unable to start SIP; check dashboard logs.');
      }
      Alert.alerts.push({
        type: 'danger',
        message: message,
      });
    };

    node.request_pending = true;
    ArchivesSpace.start_sip(node).then(on_success, on_failure);
  };
}]).

controller('ArchivesSpaceEditController', ['$uibModalInstance', 'levels', 'level', 'title', 'start_date', 'end_date', 'date_expression', 'notes', function($uibModalInstance, levels, level, title, start_date, end_date, date_expression, notes) {
  var vm = this;

  vm.levels = levels;
  vm.level = level;
  vm.title = title;
  vm.start_date = start_date;
  vm.end_date = end_date;
  vm.date_expression = date_expression;
  vm.disableNotesEdit = false;

  if (angular.isDefined(notes) && notes.length > 0) {
    // If the record has existing notes,
    // disable the fields but show the values
    vm.disableNotesEdit = true;
    let general_notes = notes.filter(note => note.type === 'odd');
    if (general_notes.length > 0) {
      vm.note = general_notes[0].content;
    }
    let use_notes = notes.filter(note => note.type === 'accessrestrict');
    if (use_notes.length > 0) {
      vm.accessrestrict_note = use_notes[0].content;
    }
  } else {
    vm.note = '';
    vm.accessrestrict_note = '';
  }

  vm.ok = function() {
    $uibModalInstance.close(vm);
  };
  vm.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
  vm.validateDate = function(value) {
    return !value || (/^\d{4}(-\d{2}(-\d{2})?)?$/.test(value) && moment(value, 'YYYY-MM-DD').isValid());
  };
}]);
