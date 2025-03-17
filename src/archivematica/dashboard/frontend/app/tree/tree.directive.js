import angular from 'angular';

angular.module('treeDirectives', []).

// When set as an attribute on an element, makes that element draggable.
// A tree-draggable element can be dropped onto a tree-droppable element.
// Use always the clone helper to make the appendTo property work for a
// better d&d representation between trees.
directive('treeDraggable', function() {
  return {
    restrict: 'A',
    link: function($scope, element, attrs) {
      jQuery(element).draggable({
        appendTo: 'body',
        containment: false,
        cursor: 'move',
        helper: 'clone',
        revert: 'invalid',
        cursorAt: {
          top: -5,
          left: -5
        }
      });
    },
  };
}).

// Marks an element as droppable; it will accept any tree-draggable element.
// The "on-drop" attribute is a function which will be called when an element
// is dropped onto it. See jquery-ui.droppable's documentation for information
// on the arguments provided to this function:
// http://api.jqueryui.com/droppable/#event-drop
// That function's `this` will be the tree-droppable element.
directive('treeDroppable', ['$parse', function($parse) {
  return {
    restrict: 'A',
    link: function($scope, element, attrs) {
      var drop_fn = $parse(attrs.onDrop)($scope);

      jQuery(element).droppable({
        drop: drop_fn.bind($scope.node),
        // The default tolerance requires 50% of the draggable element to be
        // intersecting with the droppable element. This is pretty hard to achieve
        // with the way we're rendering element names. The "pointer" option checks
        // for mouse cursor position instead, which is more reliable for us.
        tolerance: 'pointer',
        hoverClass: 'expecting'
      });
    },
  };
}]);
