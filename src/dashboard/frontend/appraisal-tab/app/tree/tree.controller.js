import angular from 'angular';

angular.module('treeController', []).

// Handles fetching the data for the transfer backlog tree view.
controller('TreeController', ['$scope', 'SelectedFiles', 'Transfer', function($scope, SelectedFiles, Transfer) {
  // angular-tree-view options
  $scope.options = {
    dirSelectable: true,
    multiSelection: true,
    equality: function(a, b) {
      if (a === undefined || b === undefined) {
        return false;
      }
      return a.id === b.id;
    },
    injectClasses: {
      li: 'file',
    },
  };
  // Hides objects with display set to "false"
  $scope.filter_expression = {display: true};
  $scope.filter_comparator = true;

  $scope.remove_tag = function(id, tag) {
    Transfer.remove_tag(id, tag);
  };

  // These functions add/remove files from the SelectedFiles service we use
  // to share files between controllers.
  var add_file = node => {
    SelectedFiles.add(node);
    if (node.children) {
      for (var i = 0; i < node.children.length; i++) {
        var child = node.children[i];
        add_file(child);
      }
    }
  };

  var remove_file = node => {
    SelectedFiles.remove(node.id);
    if (node.children) {
      for (var i = 0; i < node.children.length; i++) {
        var child = node.children[i];
        remove_file(child);
      }
    }
  };

  // TODO: * this does select all files, but it doesn't select them in the UI
  $scope.track_selected = function(node, selected) {
    if (selected) {
      add_file(node);
    } else {
      remove_file(node);
    }
  };
  $scope.transfers = Transfer;

  $scope.deselect = function() {
    SelectedFiles.selected = [];
  };

  $scope.files = SelectedFiles;
  $scope.submit = function() {
    var tag = this.tag;
    if (!tag) {
      return;
    }

    Transfer.add_list_of_tags(SelectedFiles.list_file_ids(), tag);
    this.tag = '';
  };
}]);
