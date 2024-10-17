/*
this file is part of archivematica.

Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>

archivematica is free software: you can redistribute it and/or modify
it under the terms of the gnu general public license as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

archivematica is distributed in the hope that it will be useful,
but without any warranty; without even the implied warranty of
merchantability or fitness for a particular purpose.  see the
gnu general public license for more details.

you should have received a copy of the gnu general public license
along with archivematica.  if not, see <http://www.gnu.org/licenses/>.
*/

$(function()
  {
    window.StatusView = Backbone.View.extend({

      el: '#connection-status',

      template: _.template($('#status-template').html()),

      initialize: function()
        {
          this.render();
        },

      render: function()
        {
          $(this.el).html(this.template());

          this.$led = $(this.el).find('img');
          this.$text = $(this.el).find('span');

          return this;
        },

      connect: function()
        {
          // log('Connected.');
          this.$led.attr({'src': '/media/images/bullet_green.png', 'title': gettext('Connected')});
          this.$text.text(gettext('Connected'));
        },

      startPoll: function()
        {
          // log('Start poll.');
          this.$led.attr({'src': '/media/images/bullet_orange.png', 'title': gettext('Loading')});
        },

      endPoll: function()
        {
          // log('End poll.');
        },

      text: function(message, error)
        {
          // log('Status message: ' + message + ')');

          if (true === error)
          {
            this.$led.attr({'src': '/media/images/bullet_delete.png', 'title': gettext('Disconnected')});
            this.$text.text(message);
          }
          else
          {
            this.$text.text(gettext('Connected'));
          }
        }

    });

  }
)
