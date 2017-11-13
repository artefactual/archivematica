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
        delete: '/ingest/uuid/delete/'
      }
    });

    window.SipCollection = Backbone.Collection.extend({

      model: Sip,

      url: '/ingest/status/',

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

          window.location = '/ingest/' + this.model.get('uuid') + '/';
        },

      remove: function(event)
        {
          event.preventDefault();
          event.stopPropagation();

          $(this.el).addClass('sip-removing');

          var self = this;

          $('<div>' +
              '<p><strong>' + gettext('Are you sure you want to remove this SIP from the dashboard? Note that this does not delete the SIP or related entities.') + '</strong></p>' +
              '<p>' +
                interpolate(gettext('Directory: %s'), [this.model.get('directory')]) + '<br />' +
                interpolate(gettext('UUID: %s'), [this.model.get('uuid')]) + '<br />' +
              '</p>' +
            '</div>').dialog(
            {
              modal: true,
              resizable: false,
              draggable: false,
              title: gettext('Remove SIP'),
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
                    text: gettext('Confirm'),
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
                    text: gettext('Cancel'),
                    click: function() {
                        $(this).dialog('close');
                        $(self.el).removeClass('sip-removing');
                      }
                  }]
            });
        },

       openMetadataEditor: function(event)
        {
          event.stopPropagation();
          event.preventDefault();

          var url = '/ingest/metadata/' + this.model.get('uuid') + '/';
          var self = this;

          var showDialog = function(data)
            {
              var dialog = $('<div class="metadata-dialog"></div>')
                .append(_.template($('#metadata-dialog').html(), data))
                .dialog({
                  title: gettext('Dublin Core metadata editor'),
                  width: 610,
                  height: 480,
                  modal: true,
                  resizable: false,
                  buttons: [
                    {
                      text: gettext('Close'),
                      click: function()
                        {
                          $(this).dialog('close');
                        }
                    },
                    {
                      text: 'Save',
                      click: function()
                        {
                          $.ajax({
                            context: this,
                            type: 'POST',
                            dataType: 'json',
                            data: $(this).find('form').serialize(),
                            success: function()
                              {
                                $(this).dialog('close');
                              },
                            error: function()
                              {
                                alert(gettext('Error'));
                              },
                            url: url});
                        }
                    }]
                });

              if (self.model.jobs.detect(function(job)
                {
                  return job.get('type') === 'Normalize submission documentation to preservation format';
                }))
              {
                dialog.find('input, select, textarea').prop('disabled', true).addClass('disabled');
                dialog.dialog('option', 'buttons', dialog.dialog('option', 'buttons').splice(0,1));
              }
            };

          $.ajax({
            type: 'GET',
            dataType: 'json',
            success: function(data)
              {
                showDialog(data);
              },
            url: url
          });

        }
    });

    window.JobView = BaseJobView.extend({

      className: 'job',

      events: {
        'click .btn_show_tasks': 'showTasks',
        'click .btn_normalization_report': 'normalizationReport',
        'click .btn_as_upload': 'as_match',
        'click .btn_atk_upload': 'atk_match',
        'change select': 'action'
      },

      template: _.template($('#job-template').html()),

      render: function()
        {
          $el = $(this.el);
          $el.html(this.template(this.model.toJSON()));
          $el.css('background-color', this.getStatusColor(this.model.get('currentstep')));

          var choices = this.model.get('choices');
          if (choices)
          {
            var $select = $('<select />').append('<option>' + gettext('Actions') + '</option>')
              , numberOfChoices = Object.keys(choices).length;

            // use pop-up action selector for long choice lists
            if (numberOfChoices >= 10)
            {
              var statusObject = {};
              this.activateEnhancedActionSelect($select, statusObject);
            }

            for (var code in choices)
            {
              $select.append('<option value="' + code + '">- ' + choices[code] + '</option>');
            }

            this.$('.job-detail-actions').append($select);
          }

          if ('Approve normalization' == this.model.get('type'))
          {
            this.$('.job-detail-actions')
              .append('<a class="btn_normalization_report" href="#" title="' + gettext('Report') + '"><span>' + gettext('Report') + '</span></a>');
          }

          var message = gettext('Match DIP objects to resources');
          if ('Choose Config for ArchivesSpace DIP Upload' == this.model.get('type'))
          {
            this.$('.job-detail-actions')
            .append('<a class="btn_as_upload" href="#" title="' + message + '"><span>' + message + '</span>');
          }

          if ('Choose Config for Archivists Toolkit DIP Upload' == this.model.get('type'))
          {
            this.$('.job-detail-actions')
            .append('<a class="btn_atk_upload" href="#" title="' + message + '"><span>' + message + '</span>');
          }

          this.$('.job-detail-microservice > a').tooltip();

          this.$('.job-detail-actions > a').tooltip();

          return this;
        },

      action: function(event)
        {
          var $select = $(event.target)
            , value = $select.val()
            , self = this;

          // Define function to execute
          var executeCommand = function(context)
            {
              $.ajax({
                context: self,
                data: { uuid: self.model.get('uuid'), choice: value, uid: self.uid},
                type: 'POST',
                success: function(data)
                  {
                    context.model.set({ 'currentstep': this.model.sip.statuses['STATUS_EXECUTING_COMMANDS'] });

                    context.model.sip.view.updateIcon();

                    // get rid of select, etc.
                    self.$('.job-detail-actions').empty();
                  },
                url: '/mcp/execute/',
                async: false
              });
            };

          // redict to object/resource mapping pages
          if ('- Upload DIP to Archivists Toolkit' == $select.find('option:selected').text())
          {
            $('body').html('<h1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + gettext('Loading...') + '</h1>');
            window.location.href = '/ingest/' + this.model.sip.get('uuid') + '/upload/atk/';
          }

          // redirect to object/resource mapping pages
          if ('- Upload DIP to ArchivesSpace' == $select.find('option:selected').text())
          {
            $('body').html('<h1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + gettext('Loading...') + '</h1>');
            window.location.href = '/ingest/' + this.model.sip.get('uuid') + '/upload/as/';
          }

          // if ('Upload DIP' == this.model.get('type') && 13 == value)
          if ('- Upload DIP to AtoM' == $select.find('option:selected').text())
          {
            var modal = $('#upload-dip-modal');
            var input = modal.find('input');
            var process = false;
            var url = '/ingest/' + this.model.sip.get('uuid') + '/upload/';
            var self = this;

            modal

              .on('shown.bs.modal', function()
                {
                  $(this).find('input').first().focus();
                })

              .one('show.bs.modal', function()
                {
                  var xhr = $.ajax(url, { type: 'GET' });
                  xhr
                    .done(function(data)
                      {
                        if (data.target)
                        {
                          input.filter(':text').val(data.target);
                        }
                      });
                })

              .one('hidden.bs.modal', function()
                {
                  input.filter(':text').val('');
                  input.filter(':checkbox').prop('checked', false);
                  $select.val(0);
                  modal.find('a.primary, a.secondary').unbind('click');
                })

              .find('a.btn-primary').bind('click', function(event)
                {
                  event.preventDefault();

                  var target = input.filter(':text').val()
                  if (!target)
                  {
                    return;
                  }

                  $('#upload-dip-modal-spinner').show();

                  // Chained XHR calls. Eventually, we should simplify this on the server side.
                  $.when(
                      $.ajax({ type: 'GET', url: '/ingest/upload/url/check/', data: { target: target } }),
                      $.ajax({ type: 'POST', url: url, data: { target: target } })
                    ).done(function(resp1, resp2) {

                      if (resp2[0].ready) {
                        executeCommand(self);
                      }

                    }).fail(function(resp1, resp2) {

                      alert(gettext('There was a problem attempting to reach the destination URL.'));

                    }).always(function() {

                      modal.modal('hide');
                      $select.val(0);

                  });
                })
              .end()

              .find('a.secondary').bind('click', function(event)
                {
                  event.preventDefault();
                  $select.val(0);
                  modal.modal('hide');
                })
              .end()

              .modal('show');

            return false;
          }

          executeCommand(this);
        },

      normalizationReport: function(event)
        {
          event.preventDefault();

          var url = '/ingest/normalization-report/' + this.model.sip.get('uuid') + '/';
          window.open(url, '_blank');
          window.focus();
        },

      as_match: function(event)
        {
          event.preventDefault();

          var url = '/ingest/' + this.model.sip.get('uuid') + '/upload/as/';
          window.open(url, '_blank');
          window.focus();
        },

      atk_match: function(event)
        {
          event.preventDefault();

          var url = '/ingest/' + this.model.sip.get('uuid') + '/upload/atk/';
          window.open(url, '_blank');
          window.focus();
        },

    });

    window.AppView = BaseAppView.extend({
      el: $('#sip-container'),
      pagingCookie: 'archivematicaCurrentIngestPage',
      unitType: 'SIP'
    });

    $.fn.tooltip = tooltipPlugin;
    window.onresize = optimizeWidth;
    window.onload = optimizeWidth;

    $(document).ready(function()
      {
        // Create modal
        $('#upload-dip-modal')
          .modal({
            show: false,
            backdrop: true,
            keyboard: true
          });
      });

  }
);
