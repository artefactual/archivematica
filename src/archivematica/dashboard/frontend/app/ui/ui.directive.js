import angular from 'angular';

angular.module('uiDirectives', []).

// The <ui-minimize-bar> and <ui-minimize-panel> directives allow the creation of
// elements which can be displayed and hidden via a set of buttons.
//
// <ui-minimize-bar> produces a horizontal div of buttons, one for every
// <ui-minimize-panel>. Clicking one of those buttons toggles the display
// of a panel on or off.
directive('uiMinimizeBar', [function() {
  return {
    restrict: 'E',
    transclude: true,
    templateUrl: 'ui/minimize-bar.html',
    controller: function($scope) {
      var panes = $scope.panes = [];

      $scope.toggle = function(pane) {
        pane.selected = !pane.selected;
        var width = 100 / panes.filter(e => e.selected).length + '%';
        // Update child element widths
        angular.forEach(panes, p => p.width = width);
      };

      this.addPane = function(pane, open) {
        panes.push(pane);
        if (open) {
          $scope.toggle(pane);
        }
      };
    },
  };
}]).

// Every <ui-minimize-panel> element produces a new togglable panel.
// These panels will all be displayed in a row horizontally, and will adjust their
// size as new panels are added or removed.
// A button to display/collapse the panel will be generated in the <ui-minimize-bar>
// element.
// The "title" attribute controls the display title in the panel's header and in
// the <ui-minimize-bar>'s button.
// The "open" attribute, set to "true" or "false", controls whether this panel
// should be open by default.
directive('uiMinimizePanel', [function() {
  return {
    require: '^uiMinimizeBar',
    restrict: 'E',
    transclude: true,
    scope: {
      title: '@',
    },
    templateUrl: 'ui/minimize-panel.html',
    link: function(scope, element, attrs, minimizeBar) {
      minimizeBar.addPane(scope, attrs.open === 'true');
    },
  };
}]).

directive('ngConfirmClick', [function() {
  // From http://zachsnow.com/#!/blog/2013/confirming-ng-click/
  return {
    priority: -1,
    restrict: 'A',
    link: function(scope, element, attrs) {
      element.bind('click', e => {
        var message = attrs.ngConfirmClick;
        if(message && !confirm(message)){
          e.stopImmediatePropagation();
          e.preventDefault();
        }
      });
    }
  };
}]);
