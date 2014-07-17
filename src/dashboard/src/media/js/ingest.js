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
              '<p><strong>Are you sure you want to remove this SIP from the dashboard? Note that this does not delete the SIP or related entities.</strong></p>' +
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
                  title: 'Dublin Core metadata editor',
                  width: 610,
                  height: 480,
                  modal: true,
                  resizable: false,
                  buttons: [
                    {
                      text: 'Close',
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
                                alert("Error.");
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
        'click .btn_browse_job': 'browseJob',
        'click .btn_approve_job': 'approveJob',
        'click .btn_reject_job': 'rejectJob',
        'click .btn_show_tasks': 'showTasks',
        'click .btn_normalization_report': 'normalizationReport',
        'change select': 'action'
      },

      template: _.template($('#job-template').html()),

      render: function()
        {
          var jobData = this.model.toJSON();

          if (
            jobData.type == 'Access normalization failed - copying'
            || jobData.type == 'Preservation normalization failed - copying'
            || jobData.type == 'thumbnail normalization failed - copying'
          ) {
            jobData.currentstep = 'Failed';
          }

          $(this.el).html(this.template(jobData));

          $(this.el).css(
            'background-color',
            this.getStatusColor(jobData.currentstep)
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
              .append('<a class="btn_normalization_report" href="#" title="Report"><span>Report</span></a>');
          }

          this.$('.job-detail-microservice > a').tooltip();

          this.$('.job-detail-actions > a').twipsy();

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
                    context.model.set({
                      'currentstep': 'Executing command(s)',
                      'status': 0
                    });

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
            $('body').html('<h1>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Loading...</h1>');
            window.location.href = '/ingest/' + this.model.sip.get('uuid') + '/upload/atk/';
          }

          // if ('Upload DIP' == this.model.get('type') && 13 == value)
          if ('- Upload DIP to Atom' == $select.find('option:selected').text())
          {
            var modal = $('#upload-dip-modal');
            var input = modal.find('input');
            var process = false;
            var url = '/ingest/' + this.model.sip.get('uuid') + '/upload/';
            var self = this;

            modal

              .on('shown', function()
                {
                  $(this).find('input').first().focus();
                })

              .one('show', function()
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

              .one('hidden', function()
                {
                  input.filter(':text').val('');
                  input.filter(':checkbox').prop('checked', false);
                  $select.val(0);
                  modal.find('a.primary, a.secondary').unbind('click');
                })

              .find('a.primary').bind('click', function(event)
                {
                  event.preventDefault();

                  if (input.filter(':text').val())
                  {
                    $('#upload-dip-modal-spinner').show();
                    // get AtoM destination URL (so we can confirm it's up)
                    $.ajax({
                      url: '/ingest/upload/url/check/?target=' + encodeURIComponent(input.filter(':text').val()),
                      type: 'GET',
                      success: function(status_code_from_url_check)
                        {
                          if (status_code_from_url_check != '200') {
                            $('#upload-dip-modal-spinner').hide();
                            alert('There was a problem attempting to reach the destination URL.');
                          } else {
                                  var xhr = $.ajax(url, { type: 'POST', data: {
                                    'target': input.filter(':text').val() }})

                                    .done(function(data)
                                      {
                                        if (data.ready)
                                        {
                                          executeCommand(self);
                                        }
                                      })
                                    .fail(function()
                                      {
                                        alert("Error.");
                                        $select.val(0);
                                      })
                                    .always(function()
                                      {
                                        modal.modal('hide');
                                      });
                          }
                        }
                    });
                  }
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
        }

    });

    window.DirectoryBrowserView = BaseDirectoryBrowserView.extend({
      template: _.template($('#directory-browser-template').html())
    });

    window.AppView = BaseAppView.extend({
      el: $('#sip-container'),
      pagingCookie: 'archivematicaCurrentIngestPage'
    });

    $.fn.tooltip = tooltipPlugin;
    window.onresize = optimizeWidth;
    window.onload = optimizeWidth;

    $(document).ready(function()
      {
        // Create modal
        $('#upload-dip-modal')
          .modal({
            backdrop: true,
            keyboard: true
          });
      });

  }
);
