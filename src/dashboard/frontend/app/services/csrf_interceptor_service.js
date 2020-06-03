import angular from 'angular';

angular.module('csrfInterceptorService', [require('angular-cookies')]).
factory('CsrfInterceptor', ['$cookies', function($cookies) {
  return {
    'request': function(config) {
      if (['POST', 'PUT', 'DELETE'].indexOf(config.method) !== -1) {
        config.headers['X-CSRFToken'] = $cookies.get('csrftoken');
      }
      return config;
    }
  };
}]).
config(function($httpProvider) {
  $httpProvider.interceptors.push('CsrfInterceptor');
});
