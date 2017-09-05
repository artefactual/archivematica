import angular from 'angular';

angular.module('alertController', ['alertService']).

controller('AlertDisplayController', ['Alert', function(Alert) {
  var vm = this;

  vm.alert = Alert;
  vm.remove = index => {
    Alert.alerts.splice(index, 1);
  };
}]);
