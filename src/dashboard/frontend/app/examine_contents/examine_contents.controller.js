import angular from 'angular';

angular.module('examineContentsController', []).

// Controls the table which displays bulk_extractor log contents.
controller('ExamineContentsController', ['$routeSegment', 'SelectedFiles', 'Transfer', function($routeSegment, SelectedFiles, Transfer) {
  var vm = this;

  vm.$routeSegment = $routeSegment;
  vm.type = $routeSegment.$routeParams.type;
  vm.SelectedFiles = SelectedFiles;

  vm.selected = [];
  vm.all_selected = false;

  vm.select_all = files => {
    if (!vm.all_selected) {
      vm.selected = files.map(file => file.id);
      vm.all_selected = true;
    } else {
      vm.selected = [];
      vm.all_selected = false;
    }
  };

  vm.submit = ids => {
    var tag = this.tag;
    if (!tag) {
      return;
    }

    Transfer.add_list_of_tags(ids, tag);
    this.tag = '';
  };

  vm.cutRelativePath = relative_path => {
    // Return only the part after '/objects/',
    // using pop to return the full path otherwise
    return relative_path.split('/objects/').pop();
  };
}]).

controller('ExamineContentsFileController', ['$routeSegment', 'File', function($routeSegment, File) {
  var vm = this;

  vm.id = $routeSegment.$routeParams.id;
  vm.type = $routeSegment.$routeParams.type;
  File.bulk_extractor_info(vm.id, [vm.type]).then(data => {
    vm.file = data;
  });
}]);
