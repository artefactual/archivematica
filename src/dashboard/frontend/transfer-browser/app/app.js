import angular from 'angular';
import 'angular-gettext';
import 'angular-tree-control';
// FIXME: doing this clashes with the dashboard's global bootstrap;
//        we should find a better fix for this at some point.
// import 'bootstrap';
import 'restangular';

// services
import './services/browse.service';
import './services/source_locations.service';
import './services/transfer.service';

// controllers
import './browse/browse.controller';
import './header/header.controller';

export default angular.module('transferBrowse', [
  'gettext',
  'restangular',
  'treeControl',
  'services.browse',
  'services.source_locations',
  'services.transfer',
  'controllers.browse',
  'controllers.header',
]).

run(function ($window, gettextCatalog) {
  // Look up current language, fallback to English
  var currentLanguage;
  try {
      currentLanguage = $window.DashboarConfig.currentLanguage
  } catch (err) {
      currentLanguage = 'en';
  }
  gettextCatalog.setCurrentLanguage(currentLanguage);

  // Load translations
  for (let [langCode, translations] of Object.entries(require('json!./locale/translations.json'))) {
      gettextCatalog.setStrings(langCode, translations);
  }
}).

config(['RestangularProvider', function(RestangularProvider) {
  RestangularProvider.setRequestSuffix('/');
}]);
