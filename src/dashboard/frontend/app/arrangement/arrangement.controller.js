var path = require('path');
import angular from 'angular';
import '../vendor/angular-ui-bootstrap/ui-bootstrap-custom-tpls-0.14.3.min.js';

angular.module('arrangementController', ['sipArrangeService', 'ui.bootstrap', require('angular-cookies')]).

// This controller is responsible for the appraisal tab's implementation of SIP arrange.
// It doesn't have its own partial, and its scope is located in front_page/appraisal_tab.html
controller('ArrangementController', ['$scope', 'gettextCatalog', '$uibModal', '$cookies', 'Alert', 'Transfer', 'SipArrange', 'Tag', function($scope, gettextCatalog, $uibModal, $cookies, Alert, Transfer, SipArrange, Tag) {
  var vm = this;

  // Watch the object with tag updates shared by the Transfer service
  // and update the vm.data structure accordingly
  vm.transfer = Transfer;
  $scope.$watch('vm.transfer.tag_updates', tag_updates => {
    if (tag_updates) {
      Object.keys(tag_updates).forEach(key => {
        if (vm.data !== undefined) {
          // TODO: profile this, reloading the whole tree
          // for a single tag update might be expensive
          vm.update_element_tags(vm.data, tag_updates);
        }
      });
    }
  }, true);

  vm.update_element_tags = function(elements, tag_updates) {
    elements.forEach(element => {
      const {file_uuid, tags} = element.properties;
      if (file_uuid !== undefined &&
          file_uuid in tag_updates &&
          tags !== tag_updates[file_uuid]) {
        element.properties.tags = tag_updates[file_uuid];
      }
      if (element.has_children) {
        vm.update_element_tags(element.children, tag_updates);
      }
    });
  };

  vm.remove_tag = ($event, node, tag) => {
    $event.stopPropagation();
    if (node.properties.file_uuid !== undefined) {
      var file_uuid = node.properties.file_uuid;
      try {
        // if the file is loaded in the Backlog pane
        // use the Transfer service to remove the tag
        vm.transfer.remove_tag(file_uuid, tag);
        // refresh the node's parent
        vm.update_element_tags([node], vm.transfer.tag_updates);
      } catch(err) {
        // otherwise calculate the new tags and
        // submit them using the Tag service
        var tags = node.properties.tags || [];
        var new_tags = tags.filter(record_tag => record_tag !== tag);
        var tag_updates = {};
        tag_updates[file_uuid] = new_tags;
        // refresh the node's parent
        vm.update_element_tags([node], tag_updates);
        Tag.submit(file_uuid, new_tags);
      }
    }
  };

  var show_wait_for_sip_alert = function() {
    Alert.alerts.push({
      'type': 'info',
      'message': gettextCatalog.getString('Please wait while the SIP is started'),
      'show_spinner': true,
    });
  };

  vm.create_sip_from_tag = function() {
    // if there's a SIP already started ask for confirmation
    if (vm.data.length > 0) {
      if (!confirm(gettextCatalog.getString('Are you sure you want to discard the current directory?'))) {
        return;
      }
      // delete existing UI data
      vm.data.forEach(directory => {
        vm.delete_directory(directory);
      });
    }
    show_wait_for_sip_alert();
    const tag = vm.create_sip_tag;
    if (!tag) {
      return;
    }
    // TODO: sanitize tag
    const title = tag;
    const full_path = tag;
    SipArrange.create_directory('/arrange/' + full_path, title, undefined).then(result => {
      // look for files containing the tag in all the transfers and
      // store all the promises to create directories and copy files
      let create_directory_promises = [];
      let copy_to_arrange_promises = [];
      let files_grouped_by_directory = {};
      let arrange_sources = [];
      let arrange_destinations = [];
      angular.forEach(vm.transfer.id_map, file => {
        if (file.type === 'file' &&
            file.tags !== undefined &&
            file.tags.includes(tag)) {
          let parent_path = path.dirname(file.relative_path);
          if (!(parent_path in files_grouped_by_directory)) {
            files_grouped_by_directory[parent_path] = [];
          }
          files_grouped_by_directory[parent_path].push(file);
        }
      });
      // filter directories to get only the deepest leaves
      let unique_directories = Object.keys(files_grouped_by_directory).filter(function(directory, i, arr) {
        let is_repeated = false;
        arr.forEach(function(other_directory) {
          if (other_directory !== directory && other_directory.startsWith(directory)) {
            is_repeated = true;
          }
        });
        return !(is_repeated);
      });
      // create a single promise for creating each unique directory
      create_directory_promises.push(
        SipArrange.create_directory(
          unique_directories.map(directory => {
            return '/arrange/' + full_path + '/' + directory + '/';
          }),
          undefined,
          undefined
        )
      );
      // get all the arrange sources and destinations in each directory
      Object.keys(files_grouped_by_directory).forEach(directory => {
        let directory_arrange_path = '/arrange/' + full_path + '/' + directory + '/';
        files_grouped_by_directory[directory].forEach(file => {
          let paths = generate_files_list(file, '/originals/', directory_arrange_path);
          arrange_sources = arrange_sources.concat(paths.source);
          arrange_destinations = arrange_destinations.concat(paths.destination);
        });
      });
      // create a single promise with all the arrange sources and destinations
      copy_to_arrange_promises.push(
        SipArrange.copy_to_arrange(arrange_sources, arrange_destinations)
          .then(on_copy_success, on_copy_failure)
      );
      let on_success = success => {
        Alert.alerts.push({
          'type': 'success',
          'message': gettextCatalog.getString('SIP successfully started!'),
        });
      };
      let on_failure = error => {
        Alert.alerts.push({
          'type': 'danger',
          'message': gettextCatalog.getString('SIP could not be started! Check dashboard logs.'),
        });
      };
      // wait that all the promises for creating directories resolve first
      // then wait for all the promises to copy file
      // and finally start creating the SIP
      Promise.all(create_directory_promises).then(function() {
        Promise.all(copy_to_arrange_promises).then(function() {
            SipArrange.start_sip('/arrange/' + full_path + '/').then(on_success, on_failure).then(function() {
              // hide elements from the UI so user
              // doesn't try to start it again
              vm.data = {};
            });
        });
      });
      // reset the tags dropdown value
      vm.create_sip_tag = '';
    });
  };

  var load_data = () => {
    SipArrange.list_contents().then(directories => {
      vm.data = directories;
    });
  };

  // angular-tree-view options
  vm.options = {
    dirSelectable: true,
    isLeaf: node => {
      return !node.has_children;
    },
  };
  // Filters the displayed tree to omit items with the display property set to false
  vm.filter_expression = {display: true};
  vm.filter_comparator = true;

  vm.refresh = node => {
    if (node) {
      load_element_children(node);
    } else {
      load_data();
    }
  };

  var load_element_children = node => {
    var path = '/arrange/' + node.path;
    SipArrange.list_contents(path, node).then(entries => {
      // if the entry has a file_uuid load its tags in the properties
      entries.forEach(function(entry) {
        if (entry.properties !== undefined &&
            entry.properties.file_uuid !== undefined) {
          Tag.get(entry.properties.file_uuid).then(function(tags) {
            entry.properties.tags = tags;
          });
        }
      });
      node.children = entries;
      node.children_fetched = true;
    });
  };

  vm.on_toggle = (node, expanded) => {
    if (!expanded || node.children_fetched) {
      return;
    }
    load_element_children(node);
  };

  vm.create_directory = parent => {
    var path = prompt(gettextCatalog.getString('Name of new directory?'));
    if (!path) {
      return;
    }

    if (parent === undefined) {
      var target = vm.data;
      var full_path = path;
    } else {
      var target = parent.children;
      var full_path = parent.path + '/' + path;
    }

    SipArrange.create_directory('/arrange/' + full_path, path, parent).then(result => {
      target.push(result);
    });
  };

  vm.delete_directory = element => {
    SipArrange.remove('/arrange/' + element.path).then(success => {
      // `element.parent` is undefined if this is a root-level directory
      var parent = element.parent ? element.parent.children : vm.data;

      var idx = parent.indexOf(element);
      parent.splice(idx, 1);
      vm.selected = undefined;
    });
  };

  var hide_elements = node => {
    node.display = false;
    if (node.children) {
      for (var i = 0; i < node.children.length; i++) {
        hide_elements(node.children[i]);
      }
    }
  };

  vm.start_sip = directory => {
    var on_success = success => {
      // Hide elements from the UI so user doesn't try to start it again
      hide_elements(directory);

      Alert.alerts.push({
        'type': 'success',
        'message': gettextCatalog.getString('SIP successfully started!'),
      });
    };

    var on_failure = error => {
      var message = gettextCatalog.getString('SIP could not be started! Check dashboard logs.');

      if (error.hasOwnProperty("data") && error.data.hasOwnProperty("code") && "ERR_NO_FILES" == error.data.code) {
        message = gettextCatalog.getString('It is not possible to create an empty SIP.');
      }

      Alert.alerts.push({
        'type': 'danger',
        'message': message,
      });
    };

    show_wait_for_sip_alert();
    SipArrange.start_sip('/arrange/' + directory.path + '/').then(on_success, on_failure);
  };

  var basename = path => path.replace(/\\/g, '/').replace( /.*\//, '' );

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

  // Called when files are dropped from either the transfer backlog
  // or from elsewhere in arrange. Dispatches to the separate
  // functions below.
  vm.drop = function(unused, ui) {
    if (ui.draggable.attr('file-type') === 'arrange') {
      return drop_from_arrange.apply(this, [unused, ui]);
    } else {
      return drop_from_backlog.apply(this, [unused, ui]);
    }
  };

  vm.open_edit_metadata_modal = function(options, selected_option) {
    return $uibModal.open({
      templateUrl: 'arrangement/edit_metadata_form.html',
      controller: 'ArrangementEditMetadataController',
      controllerAs: 'form',
      resolve: {
        levels: () => {
          return options
        },
        level: () => {
          return selected_option;
        }
      }
    });
  };

  vm.edit_metadata_handler = function(node) {
    var node_title = node.title,
      node_path = node.path,
      node_level_of_description;
    if (node.properties !== undefined &&
        node.properties.levelOfDescription !== undefined) {
      // this property represents the label of the level
      // of description not its uuid
      node_level_of_description = node.properties.levelOfDescription;
    }
    return function(levels_of_description) {
      // levels_of_description is an array of {uuid: name} objects
      // so we create an array of options to use in the form menu
      // and a dictionary indexed by label
      var node_option, menu_options = [];
      levels_of_description.forEach(function(e) {
        var option = {
          'value': Object.keys(e)[0],
          'label': Object.values(e)[0]
        };
        if (option.label === node_level_of_description) {
          node_option = option;
        };
        menu_options.push(option);
      });
      // create edit metadata modal and open it
      var form = vm.open_edit_metadata_modal(menu_options, node_option);
      // handle form submission
      form.result.then(form_submission => {
        $.ajax({
          url: '/api/filesystem/metadata/',
          type: 'POST',
          headers: {'X-CSRFToken': $cookies.get('csrftoken')},
          cache: false,
          data: {
            'path': '/arrange/' + node_path,
            'level_of_description': form_submission.level.value
          },
          error: error => {
            Alert.alerts.push({
             'type': 'danger',
             'message': gettextCatalog.getString('Unable to submit edits to record "{{title}}"; check dashboard logs.', { title: node_title })
            });
          },
          // always refresh the tree after submission
          complete: () => vm.refresh()
        });
      });
    };
  };

  vm.edit_metadata = function(node) {
    SipArrange.get_atom_levels_of_description().then(
      vm.edit_metadata_handler(node), // success
      function() { // error
        Alert.alerts.push({
          'type': 'danger',
          'message': gettextCatalog.getString('Error fetching levels of description')
        });
        vm.refresh();
      }
    );
  };

  var on_copy_failure = error => {
    Alert.alerts.push({
      'type': 'danger',
      'message': gettextCatalog.getString('Failed to copy files to SIP arrange; check Dashboard logs.'),
    });
  };
  var on_copy_success = success => {
    // Reload the tree, rather than recreating the structure locally,
    // since it's possible the structure of the dragged files
    // may differ from the structure of what actually entered arrange.
    // TODO: when bugs about dragging contents into the wrong directory are
    //       resolved, maybe want to reload only the directory into which
    //       contents were dragged and not the entire tree.
    load_data();
  };

  var drop_from_backlog = function(unused, ui) {
    var file_uuid = ui.draggable.attr('uuid');
    var file = Transfer.id_map[file_uuid];

    let paths = generate_files_list(file,
      '/originals/',
      '/arrange/' + this.path + '/'
    );

    SipArrange.copy_to_arrange(paths.source, paths.destination).then(on_copy_success, on_copy_failure);
  };

  var drop_from_arrange = function(unused, ui) {
    var path = ui.draggable.attr('file-path');

    SipArrange.copy_to_arrange('/arrange/' + path, '/arrange/' + this.path + '/').then(on_copy_success, on_copy_failure);
  };

  load_data();
}]).

controller('ArrangementEditMetadataController', ['$uibModalInstance', 'levels', 'level', function($uibModalInstance, levels, level) {
  var vm = this;

  vm.levels = levels;
  vm.level = level;

  vm.ok = function() {
    $uibModalInstance.close(vm);
  };
  vm.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };

}]);
