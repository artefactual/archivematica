// Styles
import './app.css';
import './browser.css';
import 'font-awesome/css/font-awesome.min.css';
import 'angular-tree-control/css/tree-control.css';
import 'angular-tree-control/css/tree-control-attribute.css';

// Angular must be available to cache the partials
import 'angular';

// Partials
import analysisTemplate from './analysis/analysis.html';
import archivesSpaceFormTemplate from './archivesspace/form.html';
import editMetadataFormTemplate from './arrangement/edit_metadata_form.html';
import examineContentsTemplate from './examine_contents/examine_contents.html';
import fileInfoTemplate from './examine_contents/file_info.html';
import appraisalTabTemplate from './front_page/appraisal_tab.html';
import transferBrowserTemplate from './front_page/transfer_browser.html';
import previewTemplate from './preview/preview.html';
import reportFormatTemplate from './report/format.html';
import reportTagsTemplate from './report/tags.html';
import minimizeBarTemplate from './ui/minimize-bar.html';
import minimizePanelTemplate from './ui/minimize-panel.html';
import formatsByFilesTemplate from './visualizations/formats_by_files.html';
import formatsBySizeTemplate from './visualizations/formats_by_size.html';
import visualizationsTemplate from './visualizations/visualizations.html';

// Third-party modules
import angular from 'angular';
import './vendor/angular-charts/angular-charts.js';
import 'angular-gettext';
import 'angular-route';
import 'angular-route-segment';
import 'angular-tree-control/angular-tree-control.js';
import 'angular-tree-control/context-menu.js';
import 'angular-ui-validate';
import 'angular-ui-bootstrap';
import 'd3';
import 'moment';
import 'restangular';

// Controllers
import './alert/alert.controller.js';
import './analysis/analysis.controller.js';
import './archivesspace/archivesspace.controller.js';
import './arrangement/arrangement.controller.js';
import './browse/browse.controller';
import './examine_contents/examine_contents.controller.js';
import './facet_selector/facet_selector.controller.js';
import './file_list/file_list.controller.js';
import './header/header.controller';
import './preview/preview.controller.js';
import './report/report.controller.js';
import './search/search.controller.js';
import './tree/tree.controller.js';
import './visualizations/visualizations.controller.js';

// Directives
import './checklist/checklist.directive.js';
import './tree/tree.directive.js';
import './ui/ui.directive.js';

// Filters
import './filters/aggregation.filter.js';
import './filters/facet.filter.js';

// Services
import './services/alert.service.js';
import './services/archivesspace.service.js';
import './services/browse.service.js';
import './services/facet.service.js';
import './services/file.service.js';
import './services/selected.service.js';
import './services/sip_arrange.service.js';
import './services/source_locations.service.js';
import './services/tag.service.js';
import './services/transfer.service.js';
import './services/transfer_browser_transfer.service.js';

// Misc
import './components/version/interpolate-filter.js';
import './components/version/version-directive.js';
import './components/version/version.js';

// Declare app level module which depends on views, and components
module.exports = angular.module('dashboard', [
  'ngRoute',
  'gettext',
  'route-segment',
  'view-segment',
  'angularCharts',
  'restangular',
  'treeControl',
  'ui.bootstrap',
  'ui.validate',
  'dashboard.version',
  'checklistDirective',
  'treeDirectives',
  'uiDirectives',
  'alertService',
  'archivesSpaceService',
  'facetService',
  'selectedFilesService',
  'sipArrangeService',
  'transferService',
  'fileService',
  'tagService',
  'facetFilter',
  'aggregationFilters',
  'analysisController',
  'alertController',
  'archivesSpaceController',
  'arrangementController',
  'examineContentsController',
  'facetController',
  'fileListController',
  'previewController',
  'reportController',
  'searchController',
  'treeController',
  'visualizationsController',
  'services.browse',
  'services.source_locations',
  'services.transfer_browser_transfer',
  'controllers.browse',
  'controllers.header',
]).

run(function ($window, gettextCatalog, $templateCache) {
    // Look up current language, fallback to English
    var currentLanguage;
    try {
      currentLanguage = $window.DashboardConfig.currentLanguage
    } catch (err) {
      currentLanguage = 'en';
    }
    gettextCatalog.setCurrentLanguage(currentLanguage);

    // Load translations
    for (let [langCode, translations] of Object.entries(require('./locale/translations.json'))) {
      gettextCatalog.setStrings(langCode, translations);
    }

    // Cache partials.
    $templateCache.put('analysis/analysis.html', analysisTemplate);
    $templateCache.put('archivesspace/form.html', archivesSpaceFormTemplate);
    $templateCache.put('arrangement/edit_metadata_form.html', editMetadataFormTemplate);
    $templateCache.put('examine_contents/examine_contents.html', examineContentsTemplate);
    $templateCache.put('examine_contents/file_info.html', fileInfoTemplate);
    $templateCache.put('front_page/appraisal_tab.html', appraisalTabTemplate);
    $templateCache.put('front_page/transfer_browser.html', transferBrowserTemplate);
    $templateCache.put('preview/preview.html', previewTemplate);
    $templateCache.put('report/format.html', reportFormatTemplate);
    $templateCache.put('report/tags.html', reportTagsTemplate);
    $templateCache.put('ui/minimize-bar.html', minimizeBarTemplate);
    $templateCache.put('ui/minimize-panel.html', minimizePanelTemplate);
    $templateCache.put('visualizations/formats_by_files.html', formatsByFilesTemplate);
    $templateCache.put('visualizations/formats_by_size.html', formatsBySizeTemplate);
    $templateCache.put('visualizations/visualizations.html', visualizationsTemplate);
}).

// See https://code.angularjs.org/1.5.11/docs/api/ng/service/$http#cross-site-request-forgery-xsrf-protection
config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken'
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken'
}]).

config(['RestangularProvider', function(RestangularProvider) {
  RestangularProvider.setRequestSuffix('/');
}]).

config(['$routeSegmentProvider', function($routeSegmentProvider) {
  $routeSegmentProvider.options.autoLoadTemplates = true;
  $routeSegmentProvider.options.strictMode = true;

  $routeSegmentProvider.
    when('/objects', 'objects').
    when('/objects/report', 'objects.report').
    when('/objects/visualizations', 'objects.visualizations').
    when('/objects/visualizations/files', 'objects.visualizations.files').
    when('/objects/visualizations/size', 'objects.visualizations.size').
    when('/tags', 'tags').
    when('/contents', 'examine_contents').
    when('/contents/:type', 'examine_contents').
    when('/contents/:id/:type', 'examine_contents.file_info').
    when('/preview', 'preview').
    when('/preview/:id', 'preview').

    segment('objects', {
      templateUrl: 'analysis/analysis.html',
      controller: 'AnalysisController',
    }).
    within().
      segment('report', {
        default: true,
        templateUrl: 'report/format.html',
        controller: 'ReportController',
      }).
      segment('visualizations', {
        templateUrl: 'visualizations/visualizations.html',
        controller: 'VisualizationsController',
      }).
      within().
        segment('files', {
          default: 'true',
          templateUrl: 'visualizations/formats_by_files.html',
        }).
        segment('size', {
          templateUrl: 'visualizations/formats_by_size.html',
        }).
      up().
    up().

    segment('tags', {
      templateUrl: 'report/tags.html',
      controller: 'ReportController',
    }).

    segment('examine_contents', {
      templateUrl: 'examine_contents/examine_contents.html',
      controller: 'ExamineContentsController',
      controllerAs: 'vm',
      dependencies: ['type'],
    }).
    within().
      segment('file_info', {
        templateUrl: 'examine_contents/file_info.html',
        controller: 'ExamineContentsFileController',
        controllerAs: 'vm',
        dependencies: ['id', 'type'],
      }).
    up().

    segment('preview', {
      templateUrl: 'preview/preview.html',
      controller: 'PreviewController',
      dependencies: ['id'],
    });
}]).

controller('MainController', ['$scope', '$routeSegment', function($scope, $routeSegment) {
  $scope.$routeSegment = $routeSegment;
}]);
