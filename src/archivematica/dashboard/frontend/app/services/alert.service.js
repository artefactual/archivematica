import angular from 'angular';

angular.module('alertService', []).

// Simple service which allows a set of alerts to be tracked in the `alerts` property.
// Provides no methods.
// Alerts are objects with the following keys:
// * type - From the types used by Bootstrap; e.g., `success`: http://getbootstrap.com/components/#alerts
// * message - The string to display to the user.
service('Alert', function() {
  return {
    alerts: [],
  };
});
