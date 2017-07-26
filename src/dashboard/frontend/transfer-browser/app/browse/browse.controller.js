import angular from 'angular';

// Controller for the tree browser component.
// This uses the SourceLocations service to reference all of the available
// source locations.
class BrowseController {
  constructor(Browse, SourceLocations, Transfer) {
    let vm = this;

    vm.browser = Browse;
    vm.transfer = Transfer;
    vm.source_location_browser = SourceLocations;
    vm.source_locations = {};
    // Fetches the available source locations from the service at startup.
    vm.fetch_source_locations();

    // angular-tree-control options
    vm.options = {
      dirSelectable: true,
      isLeaf: function(node) {
        return !node.has_children;
      },
    };

    vm.data = [];
    vm.selected = [];
  }

  browse(location_uuid) {
    let path = this.source_locations[location_uuid].path;
    this.browser.browse(location_uuid, path).then(data => {
      this.data = data;
    });
  }

  fetch_source_locations() {
    let previous_locations = this.source_locations;
    this.source_locations = {};

    this.source_location_browser.list().then(locations => {
      locations.forEach(location => {
        this.source_locations[location.uuid] = location;
      });
      // preselect the first location, and browse it's contents
      this.source_location = locations[0].uuid;
      this.browse(this.source_location);
    }, error => {
      this.source_locations = previous_locations;
    });
  }

  // One level of directories is fetched at once; when the tree is
  // expanded, children get fetched.
  on_toggle(node, expanded) {
    if (!expanded || node.children_fetched) {
      return;
    }

    let path = node.path;
    this.browser.browse(this.source_location, path).then(entries => {
      node.children = entries;
      node.children_fetched = true;
    });
  }

  zip_filter(file) {
      // Check if it's a compressed file
      if (
        file.title.endsWith('.zip') ||
        file.title.endsWith('.tgz') ||
        file.title.endsWith('.tar.gz')
      ) {
          return true;
      }
      return false;
    }

  // Determines whether a given file can be added to the transfer,
  // depending on the transfer type.
  file_can_be_added(file) {
    if (this.transfer.type === 'zipped bag') {
      return !file.directory && this.zip_filter(file);
    } else if (this.transfer.type === 'dspace') {
      return file.directory || this.zip_filter(file);
    } else {
      return file.directory;
    }
  }
}

export default angular.module('controllers.browse', ['services.browse', 'services.source_locations', 'services.transfer']).
  controller('BrowseController', BrowseController).
  name;

BrowseController.$inject = ['Browse', 'SourceLocations', 'Transfer'];
