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
                          },
                        headers: {'X-CSRFToken': getCookie('csrftoken')}

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

          var linkId = this.model.get('link_id');

          // "Approve normalization" chain link matched by its UUID.
          if (linkId == 'de909a42-c5b5-46e1-9985-c031b50e9d30')
          {
            this.$('.job-detail-actions')
              .append('<a class="btn_normalization_report" href="#" title="' + gettext('Report') + '"><span>' + gettext('Report') + '</span></a>');
          }

          var message = gettext('Match DIP objects to resources');

          // "Choose Config for ArchivesSpace DIP Upload" chain link matched by its UUID.
          if (linkId == 'a0db8294-f02a-4f49-a557-b1310a715ffc')
          {
            this.$('.job-detail-actions')
            .append('<a class="btn_as_upload" href="#" title="' + message + '"><span>' + message + '</span>');
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
                headers: {'X-CSRFToken': getCookie('csrftoken')},
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

          var chainId = $select.find('option:selected').val();
          var unitId = this.model.sip.get('uuid');

          // If the Upload DIP targets a system where manual mapping is
          // required, we forward the user to the corresponding page where
          // we're going to collect the data required and continue the work.
          //
          // In other words, we're not going to execute the next job from
          // JavaScript as we expect the pairing page to do it once the user
          // has paired the items.
          var dipUploadWithMappingPage = {
            // "Upload DIP to ArchivesSpace" chain matched by its UUID.
            '3572f844-5e69-4000-a24b-4e32d3487f82': '/ingest/' + unitId + '/upload/as/',
          }
          if (chainId in dipUploadWithMappingPage) {
            $('body').html('<h1 style="text-align: center;">' + gettext('Loading...') + '</h1>');
            event.preventDefault();
            window.location.href = dipUploadWithMappingPage[chainId];
            return false;
          }

          // "Upload DIP to AtoM/Binder" chain matched by its UUID.
          // If no identifier for the AtoM or Binder SWORD V1 deposit endpoint
          // provided at start of transfer, display a modal dialog to request
          // such here.
          if (chainId == '0fe9842f-9519-4067-a691-8a363132ae24')
          {
            // if no access system ID provided, ask for one
            var url = '/ingest/' + unitId + '/upload/';

            if (this.model.sip.attributes.access_system_id == ''
              || this.model.sip.attributes.access_system_id == null
            ) {
              var modal = $('#upload-dip-modal');
              var input = modal.find('input');
              var process = false;
              var self = this;

              // Allow <Enter> keypress to click the "Upload" button
              input.keypress(function(e) {
                if (e.which == 13) {
                  e.preventDefault();
                  modal.find('a.btn-primary').click();
                }
              });

              modal

                .on('shown', function()
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
                    if (input.filter(':text').val())
                    {
                      // get AtoM destination URL (so we can confirm it's up)
                      var xhr = $.ajax(url, {
                        type: 'POST',
                        data: {'target': input.filter(':text').val()},
                        headers: {'X-CSRFToken': getCookie('csrftoken')}
                      })
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
            } else {
              // The access system ID that the user supplies at the start of
              // transfer must contain the correct target prefix if the upload
              // is to Binder, i.e., the 'ar:' prefix for an artwork record and
              // the 'tr:' prefix for a technical record. This is explained in
              // the modal dialog help text. See templates/ingest/grid.html.
              var xhr = $.ajax(url, {
                type: 'POST',
                data: {'target': this.model.sip.attributes.access_system_id},
                headers: {'X-CSRFToken': getCookie('csrftoken')}
              }).done(function(data)
                  {
                    if (data.ready)
                    {
                      executeCommand(self);
                    }
                  })
                .fail(function()
                  {
                    alert("Error.");
                  })
            }

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
