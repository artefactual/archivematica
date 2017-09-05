import angular from 'angular';

angular.module('selectedFilesService', []).

// Tracks a list of selected files; intended to be used by the Transfer controller
// to share the list of files selected in the user interface.
service('SelectedFiles', [function() {
  return {
    // Adds a single `file` object to the list of selected files.
    // If a file with the same ID already exists in the selection,
    // it will be removed first.
    add: function(file) {
      // Remove any occurrences of this file if they already exist
      this.remove(file.id);
      this.selected.push(file);
    },
    // Removes a file with the specified `id` from the list of selected files.
    remove: function(uuid) {
      this.selected = this.selected.filter(el => el.id !== uuid);
    },
    // Lists all of the `id` values for every file in the list.
    list_file_ids: function() {
      var ids = [];
      angular.forEach(this.selected, file => {
        if (file.type === 'file') {
          ids.push(file.id);
        }
      });
      return ids;
    },
    // Attempts to locate a file with the given `id` within the file list.
    // Returns `undefined` if no matching file is present.
    get: function(id) {
      // TODO: look at optimizing file lookup-by-id if this gets used a lot
      for (var i = 0; i < this.selected.length; i++) {
        var item = this.selected[i];
        if (item.id === id) {
          return item;
        }
      }
    },
    selected: [],
  };
}]);
