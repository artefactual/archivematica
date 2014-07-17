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

$(function()
  {
    window.Sip = Sip.extend({
      methodUrl: {
        delete: '/transfer/uuid/delete/'
      }
    });

    window.SipCollection = Backbone.Collection.extend({

      model: Sip,

      url: '/transfer/status/',

      initialize: function()
        {

        },

      comparator: function(sip)
        {
          return -1 * sip.get('timestamp');
        }

    });

    window.SipView = BaseSipView.extend({

      template: _.template($('#sip-template').html()),

      initialize: function()
        {
          this.uid = this.options.uid;

          _.bindAll(this, 'render', 'update', 'updateIcon');
          this.model.view = this;
          this.model.bind('change:timestamp', this.update);
        },

      openPanel: function(event)
        {
          event.preventDefault();

          window.location = '/transfer/' + this.model.get('uuid') + '/';
        },

      remove: function(event)
        {
          event.preventDefault();
          event.stopPropagation();

          $(this.el).addClass('sip-removing');

          var self = this;

          $('<div>' +
              '<p><strong>Are you sure you want to remove this transfer from the dashboard? Note that this does not delete the transfer or related entities.</strong></p>' +
              '<p>Directory: ' + this.model.get('directory') + '<br />UUID: ' + this.model.get('uuid') + '<br />Status: ' + $(this.el).find('.sip-detail-icon-status > img').attr('title') + '</p>' +
            '</div>').dialog(
            {
              modal: true,
              resizable: false,
              draggable: false,
              title: 'Remove SIP',
              width: 480,
              close: function(event, ui)
                {
                  if (event.which !== undefined)
                  {
                    $(self.el).removeClass('sip-removing');
                  }
                },
              buttons: [
                  {
                    text: 'Confirm',
                    click: function() {

                      var $dialog = $(this);

                      self.model.destroy({
                        success: function (model, response)
                          {
                            $dialog.dialog('close');

                            setTimeout(function()
                              {
                                $(self.el).hide('blind', function()
                                  {
                                    $(this).remove();
                                  });
                              }, 250);
                          },
                        error: function(model, response)
                          {
                            $dialog.dialog('close');
                            $(self.el).removeClass('sip-removing');
                          }

                      });
                    }
                  },
                  {
                    text: 'Cancel',
                    click: function() {
                        $(this).dialog('close');
                        $(self.el).removeClass('sip-removing');
                      }
                  }]
            });
        }
    });

    window.JobView = BaseJobView.extend({

      className: 'job',

      events: {
        'click .btn_browse_job': 'browseJob',
        'click .btn_approve_job': 'approveJob',
        'click .btn_reject_job': 'rejectJob',
        'click .btn_show_tasks': 'showTasks',
        'change select': 'action'
      },

      template: _.template($('#job-template').html()),

      render: function()
        {
          $(this.el).html(this.template(this.model.toJSON()));

          $(this.el).css(
            'background-color', 
            this.getStatusColor(this.model.get('currentstep'))
          );

          // Micro-services requiring approval
          if (1 === this.model.get('status'))
          {
            this.$('.job-detail-actions')
              .append('<a class="btn_browse_job" href="#" title="Browse"><span>Browse</span></a>')
              .append('<a class="btn_approve_job" href="#" title="Approve"><span>Approve</span></a>')
              .append('<a class="btn_reject_job" href="#" title="Reject"><span>Reject</span></a>');
          }
          else
          {
            // ...
          }

          choices = this.model.get('choices');

          if (choices)
          {
            var $select = $('<select />').append('<option>Actions</option>')
              , numberOfChoices = Object.keys(choices).length
              , optionHtml;

            // use pop-up action selector for long choice lists
            if (numberOfChoices >= 10)
            {
              var statusObject = {};
              this.activateEnhancedActionSelect($select, statusObject);
            }

            for (var code in choices)
            {
              optionHtml = '<option value="' + code + '">- ' + choices[code] + '</option>';
              $select.append(optionHtml);
            }

            this.$('.job-detail-actions').append($select);
          }

          this.$('.job-detail-microservice > a').tooltip();

          return this;
        },

      action: function(event)
        {
          var value = $(event.target).val()
            , self = this;

          $.ajax({
            context: this,
            data: { uuid: this.model.get('uuid'), choice: value, uid: this.uid },
            type: 'POST',
            success: function(data)
              {
                this.model.set({
                  'currentstep': 'Executing command(s)',
                  'status': 0
                });

                this.model.sip.view.updateIcon();

                // get rid of select, etc.
                self.$('.job-detail-actions').empty();
              },
            url: '/mcp/execute/'
          });
        }

    });

    window.DirectoryBrowserView = BaseDirectoryBrowserView.extend({
      template: _.template($('#directory-browser-template').html())
    });

    window.AppView = BaseAppView.extend({
      el: $('#sip-container'),
      pagingCookie: 'archivematicaCurrentTransferPage'
    });

    $.fn.tooltip = tooltipPlugin;
    window.onresize = optimizeWidth;
    window.onload = optimizeWidth;
  }
);
