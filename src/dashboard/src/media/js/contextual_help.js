/*
This file is part of Archivematica.

Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>

Archivematica is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Archivematica is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
*/

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
      $('#contextual_help').remove();
      var helpElementId = $(self).attr('id') + '_help'
        , helpText = $('#' + helpElementId).html();

      $(self).before('<div id="contextual_help" style="float:right"></div>');
      $('#contextual_help').html(helpText);
    });
    $(this).blur(function() {
      // wait a bit to remove help in case there's links in the help that
      // can be clicked
      setTimeout(function() {
        $('#contextual_help').remove();
      }, 2000);
    });
  });
}
