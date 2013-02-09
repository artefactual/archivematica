/*
 *
 * If a form element is given the class "has_contextual_help" then if the element
 * is given focus:
 *
 * 1) An element with the form element's ID plus the string "_help" is used to
 *    contain help text. This element should probably be hidden.
 *
 * 2) A DIV of ID "contextual_help" is inserted before the form element. CSS
 *    can be used to float this DIV to the left or right.
 *
 * If the element loses focus:
 *
 * 1) The DIV of ID "contextual_help" is removed from the DOM.
 *
 */
function archivematicaEnableContextualHelp() {
  $('.has_contextual_help').each(function() {
    var self = this;
    $(this).focus(function() {
      var helpElementId = $(self).attr('id') + '_help'
        , helpText = $('#' + helpElementId).html();

      $(self).before('<div id="contextual_help" style="float:right"></div>');
      $('#contextual_help').html(helpText);
    });
    $(this).blur(function() {
      $('#contextual_help').remove();
    });
  });
}
