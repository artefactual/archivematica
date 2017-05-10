function log(message) {
  try
  {
    console.log(message);
  }
  catch (error)
  {
    try
    {
      window.opera.postError(a);
    }
    catch (error)
    {
    }
  }
}

function optimizeWidth() {
  var width = document.documentElement.clientWidth;

  if (1020 > width)
  {
    document.body.className = 'w-lte-1020';
  }
  else if (1200 > width)
  {
    document.body.className = 'w-lte-1200';
  }
  else
  {
    document.body.className = '';
  }
};

function tooltipPlugin(options)
  {
    var settings = {
      xOffset: 10,
      yOffset: 20,
      width: 280
    };

    return this.each(function()
      {
        var $this = $(this);
        var $tooltip;

        if (options)
        {
          $.extend(settings, options);
        }

        if (undefined === settings.content)
        {
          settings.content = $this.attr('title');
        }

        $this
          .attr('title', '')
          .mouseover(function(event)
            {
              $('.tooltip').remove();

              $tooltip = $('<div class="tooltip">' + (undefined !== settings.title ? '<p class="tooltip-title">' + settings.title + '</p>' : '') + '<div class="tooltip-content">' + settings.content + '</div></div>')
                .hide()
                .css({
                  top: (event.pageY - settings.xOffset) + 'px',
                  left: (event.pageX + settings.yOffset) + 'px',
                  width: settings.width + 'px'})
                .fadeIn()
                .appendTo('body');
            })
          .mouseout(function(event)
            {
              $tooltip.remove();
            })
          .mousemove(function(event)
            {
              $tooltip.css({
                top: (event.pageY - settings.xOffset) + 'px',
                left: (event.pageX + settings.yOffset) + 'px'});
            })
          .click(function(event)
            {
              event.preventDefault();
            });
      });
  };

Sip = Backbone.Model.extend({

  statuses: {
    'STATUS_UNKNOWN': 0,
    'STATUS_AWAITING_DECISION': 1,
    'STATUS_COMPLETED_SUCCESSFULLY': 2,
    'STATUS_EXECUTING_COMMANDS': 3,
    'STATUS_FAILED': 4,

    // These are only available on the client side :()
    'STATUS_REJECTED': 'Rejected'
  },

  methodUrl:
  {
    'delete': '/transfer/uuid/delete/'
  },

  sync: function(method, model, options)
    {
      if (model.methodUrl && model.methodUrl[method.toLowerCase()])
      {
        options = options || {};
        options.url = model.methodUrl[method.toLowerCase()].replace('uuid', this.get('id'));
      }

      Backbone.sync(method, model, options);
    },

  initialize: function()
    {
      this.loadJobs();
    },

  hasFinished: function(attributes)
    {
      var self = this;

      return false === attributes.jobs.some(function(job)
        {
          return -1 < jQuery.inArray(job.currentstep, [self.statuses['STATUS_EXECUTING_COMMANDS'], self.statuses['STATUS_AWAITING_DECISION']]);
        });
    },

  set: function(attributes, options)
    {
      res = Backbone.Model.prototype.set.call(this, attributes, options);

      // Update the view only if the unit is in progress
      if (!this.hasFinished(attributes) && this.hasOwnProperty('view'))
      {
        this.view.update();
      }

      return res;
    },

  loadJobs: function()
    {
      // Nested collection
      this.jobs = new JobCollection(this.get('jobs'));

      var self = this;
      this.jobs.each(function(job)
        {
          job.sip = self;
        });
    }
});

Job = Backbone.Model.extend({});

JobCollection = Backbone.Collection.extend({

  model: Job,

  comparator: function(job)
    {
      return -1 * job.get('timestamp');
    }
});

var BaseSipView = Backbone.View.extend({

  className: 'sip',

  events: {
    'click .sip-detail-directory': 'toggleJobs',
    'click .sip-detail-uuid': 'toggleJobs',
    'click .sip-detail-timestamp': 'toggleJobs',
    'click .sip-detail-actions > .btn_show_panel': 'openPanel',
    'click .sip-detail-actions > .btn_show_metadata': 'openPanel',
    'click .sip-detail-actions > .btn_remove_sip': 'remove'
  },

  render: function()
    {
      var self = this;

      $(this.el).html(this.template(this.model.toJSON()));

      this.$jobContainer = this.$('.sip-detail-job-container');

      $(this.el).hover(
        function() {
          // temporarily increase bottom margin if hovering over closed SIP container
          var nextSibling = $(self.el).next();
          if (nextSibling.children(':nth-child(2)').is(':visible')) {
            // ease in margin setting
            $(self.el).animate({
              'margin-bottom': '10px',
              queue: true
            }, 200);
          }
        },
        function() {
          // open SIP containers don't need temporary bottom margin adjustment
          if (!$(self.el).children(':nth-child(2)').is(':visible')) {
            self.updateBottomMargins();
          }
         }
      );

      // populate job container so we can see if any jobs require user action
      this.updateJobContainer();

      // if any jobs require user action, toggle the microservice group
      this.$jobContainer.find('.job-detail-currentstep[data-currentstep=' + this.model.statuses['STATUS_AWAITING_DECISION'] + ']').each(function() {
        self.doToggleJobs();
      });

      return this;
    },

  toggleJobs: function(event)
    {
      var self = this;

      event.preventDefault();
      event.stopPropagation();

      this.doToggleJobs();
    },

  doToggleJobs: function()
    {
      var self = this;

      if (this.$jobContainer.is(':visible'))
      {
        this.$jobContainer.slideUp('fast', function()
          {
            self.updateBottomMargins();
          }
        );

        $(this.el).removeClass('sip-selected');
      }
      else
      {
        this.updateJobContainer();
      }
    },

  updateJobContainer: function()
    {
      var groups = {}
        , group
        , self = this;

      // separate jobs by group
      this.model.jobs.each(function(job)
        {
          group = job.get('microservicegroup');
          groups[group] = groups[group] || new JobCollection();
          groups[group].add(job);
        }
      );

      // take note of any groups that have been open by the user before
      // we refresh the DOM
      var openGroups = [];
      $(this.$jobContainer).children('.microservicegroup').each(function () {
        // if group is open, take note of it
        var group = $(this).children(':first').children('.microservice-group-name').text()
          , visible = $(this).children(':nth-child(2)').is(':visible');

        if (visible) {
          openGroups.push(group);
        }
      });

      // refresh DOM
      this.$jobContainer.empty();

      // display groups
      for(group in groups) {
        var group = new MicroserviceGroupView({
          name: group,
          jobs: groups[group],
          uid: this.uid
        });
        group.template = _.template(
          $('#microservice-group-template').html()
        );
        this.$jobContainer.append(group.render().el);
      }

      // re-open any groups that were open before the DOM elements were refreshed
      $(this.$jobContainer).children('.microservicegroup').each(function () {
        var group = $(this).children(':first').children('.microservice-group-name').text()
          , visible = $(this).children(':nth-child(2)').is(':visible');

        // show jobs in group if group was open
        if (openGroups.indexOf(group) != -1) {
          $(this).children(':nth-child(2)').show();
        }
      });

      // open microservice if any jobs await a decision
      this.$jobContainer.find('.job-detail-currentstep[data-currentstep=' + this.model.statuses['STATUS_AWAITING_DECISION'] + ']').each(function() {
        $(this).parent().parent().show();
      });

      this.$jobContainer.slideDown('fast', function()
        {
          self.updateBottomMargins();
        }
      );
      $(this.el).addClass('sip-selected');
    },

  updateBottomMargins: function()
    {
       $('.sip').each(function()
         {
           // create bottom margin if next SIP has been toggled open
           var finalBottomMargin =
             ($(this).children(':nth-child(2)').is(':visible'))
               ? '10px'
               : '0px';

            // ease in margin setting
            $(this).animate({
              'margin-bottom': finalBottomMargin,
              queue: true
            }, 200);
         }
       );
    },

  update: function()
    {
      // Reload nested collection
      this.model.loadJobs(); // .refresh() shouldn't work here

      // Update timestamp
      this.$('.sip-detail-timestamp').html(this.getIngestStartTime());

      // Update icon
      this.updateIcon();

      if (this.$jobContainer.is(':visible'))
      {
        this.updateJobContainer();
      }
    },

  updateIcon: function()
    {
      this.$('.sip-detail-icon-status').html(this.getIcon());
    },

  getIngestStartTime: function()
    {
      // Use last micro-service timestamp
      var job = this.model.jobs.last();

      return new Date(job.get('timestamp') * 1000).getArchivematicaDateTime();
    },

  getIcon: function()
    {
      // I feel like this should go somewhere else but it's ok for now.
      var icons = new Object;
      icons[this.model.statuses['STATUS_UNKNOWN']] = 'bell.png',
      icons[this.model.statuses['STATUS_AWAITING_DECISION']] = 'bell.png',
      icons[this.model.statuses['STATUS_COMPLETED_SUCCESSFULLY']] = 'accept.png',
      icons[this.model.statuses['STATUS_EXECUTING_COMMANDS']] = 'arrow_refresh.png',
      icons[this.model.statuses['STATUS_FAILED']] = 'cancel.png',
      icons[this.model.statuses['STATUS_REJECTED']] = 'control_stop_blue.png'

      var job = this.model.jobs.first();
      var currentstep = job.get('currentstep');

      // TODO: What is this? Can't the server tell us? Seriously...
      if (job.microservicegroup == 'Reject SIP' || job.type == 'Move to the rejected directory') {
        currentstep = this.model.statuses['STATUS_REJECTED'];
      }
      if (job.microservicegroup == 'Failed transfer') {
        currentstep = this.model.statuses['STATUS_FAILED'];
      }

      var icon = 'accept.png';
      if (icons.hasOwnProperty(currentstep)) {
        icon = icons[currentstep];
      }

      return '<img src="/media/images/' + icon + '"/>';
    }
});

var MicroserviceGroupView = Backbone.View.extend({

  className: 'microservicegroup',

  initialize: function()
    {
      this.name = this.options.name || '';
      this.jobs = this.options.jobs || new JobCollection();
      this.uid  = this.options.uid;
    },

  render: function()
    {
      var self = this;

      // Render group wrapper
      $(this.el).html(this.template({ name: this.name }));

      // Add container for jobs
      var jobDiv = $('<div class="job-container"></div>').hide();
      $(this.el).append(jobDiv);

      var previewUrl = function(linkId, uuid) {
        // Store AIP
        if (linkId == '2d32235c-02d4-4686-88a6-96f4d6c7b1c3') {
          return '/ingest/preview/aip/' + uuid;
        // Approve normalization
        } else if (linkId == 'de909a42-c5b5-46e1-9985-c031b50e9d30') {
          return '/ingest/preview/normalization/' + uuid;
        // Move to the uploadedDIPs directory
        } else if (linkId == '2e31580d-1678-474b-83e5-a53d97d150f6' || linkId == 'e3efab02-1860-42dd-a46c-25601251b930') {
          return '/ingest/preview/dip/' + uuid;
        }
      }

      this.jobs.each(function(job) {

        // Render job
        var view = new JobView({ model: job, uid: self.uid });
        jobDiv.append(view.render().el);

        // "Store AIP", "Approve normalization" or
        var isStoreAIP = -1 < jQuery.inArray(job.get('link_id'), ['2d32235c-02d4-4686-88a6-96f4d6c7b1c3', 'de909a42-c5b5-46e1-9985-c031b50e9d30']) && job.get('currentstep') == job.sip.statuses['STATUS_AWAITING_DECISION'];
        var isUpload = -1 < jQuery.inArray(job.get('link_id'), ['e3efab02-1860-42dd-a46c-25601251b930', '2e31580d-1678-474b-83e5-a53d97d150f6']);

        // Add link to browse SIP before it's made into an AIP
        if (isStoreAIP || isUpload)
        {
          $(view.el)
            .children(':first')
            .children(':nth-child(2)')
            .append('&nbsp;<a href="' + previewUrl(job.get('link_id'), job.get('uuid')) + '" target="_blank" class="btn btn-default btn-xs">' + gettext('Review') + '</a>');
        }

      });

      // toggle job container when user clicks handle
      $(this.el).children(':first').click(function() {
        $(this)
          .children('.microservice-group-arrow')
          .html(jobDiv.is(':visible') ? '&#x25B8' : '&#x25BE');
        jobDiv.toggle('fast');
      });

      return this;
    }
});

var BaseJobView = Backbone.View.extend({

  initialize: function()
    {
      _.bindAll(this, 'render');
      this.model.bind('change', this.render);
      this.model.view = this;
      this.uid = this.options.uid;
    },

  taskDialog: function(data, options)
    {
      var dialog = $('<div class="task-dialog"><a name="tasks-dialog-top"></a></div>');

      if (options == undefined) {
        options = {};
      }

      if (options.width == undefined) {
        options.width = 640;
      }

      if (options.height == undefined) {
        options.height = 640;
      }

      var table = $('<table class="table"></table>');
      table.append(data);
      dialog.append(table)

      return dialog.dialog({
          title: interpolate(gettext('%(directory) &raquo; %(type) &raquo; Tasks'), {'directory': this.model.sip.get('directory'), 'type': this.model.get('type')}, true),
          width: options.width,
          height: options.height,
          modal: true,
          buttons: [
            {
              text: gettext('Close'),
              click: function() { $(this).dialog('close'); }
            }]
        });
    },

  showTasks: function(event)
    {
      event.preventDefault();

      window.open('/tasks/' + this.model.get('uuid') + '/', '_blank');
    },

  /**
   * TODO: this should be refactor to rely on CSS classes instead.
   */
  getStatusColor: function(status)
    {
      var UNKNOWN_COLOR = '#d8f2dc';

      var colors = new Object;
      colors[this.model.sip.statuses['STATUS_UNKNOWN']] = UNKNOWN_COLOR;
      colors[this.model.sip.statuses['STATUS_AWAITING_DECISION']] = '#ffffff';
      colors[this.model.sip.statuses['STATUS_COMPLETED_SUCCESSFULLY']] = '#d8f2dc';
      colors[this.model.sip.statuses['STATUS_EXECUTING_COMMANDS']] = '#fedda7';
      colors[this.model.sip.statuses['STATUS_FAILED']] = '#f2d8d8';
      colors[this.model.sip.statuses['STATUS_REJECTED']] = '#f2d8d8';

      if (colors.hasOwnProperty(status)) {
        return colors[status];
      }

      return UNKNOWN_COLOR;
    },

  // augment dashboard action select by using a pop-up with an enhanced select widget
  activateEnhancedActionSelect: function($select, statusObject)
    {
      $select.hover(function() {
        // if not showing proxy selector and modal window
        if (!statusObject.bigSelectShowing)
        {
          // clone action selector
          var $proxySelect = $select.clone();

          // display action selector in modal window
          $('<div class="modal hide" id="big-choice-select-modal"><div class="modal-header"><button type="button" class="close" id="big-choice-select-close" data-dismiss="modal">×</button><h3>' + gettext('Select an action...') + '</h3></div><div class="modal-body" id="big-choice-select-body"></div><div class="modal-footer"><a href="#" class="btn btn-default" data-dismiss="modal" id="big-choice-select-cancel">' + gettext('Cancel') + '</a></div></div>').modal({show: true});
          $('#big-choice-select-body').append($proxySelect);

          // style clone as Select2
          $proxySelect.select2();

          // proxy selections to action selector
          $proxySelect.change(function()
                  {
            $select.val($(this).val());
            $select.trigger('change');
            $('#big-choice-select-modal').remove();
          });

          // allow another instance to show if modal is closed
          $('#big-choice-select-close, #big-choice-select-cancel').click(function()
          {
            statusObject.bigSelectShowing = false;
            $('#big-choice-select-modal').remove();
          });

          // prevent multiple instances of this from displaying at once
          statusObject.bigSelectShowing = true;
        }
      });
    }
});

BaseAppView = Backbone.View.extend({

  interval: window.pollingInterval ? window.pollingInterval * 1000: 5000,

  idle: false,

  initialize: function(options)
    {
      this.statusUrl = options.statusUrl;
      this.uid       = options.uid;

      _.bindAll(this, 'add', 'remove');
      Sips.bind('add', this.add);
      Sips.bind('remove', this.remove);

      window.statusWidget = new window.StatusView();

      this.poll(true);
    },

  add: function(sip)
    {
      var view = new SipView({
        model: sip,
        uid: this.uid
      });
      var $new = $(view.render().el).hide();

      // Get the current position in the collection
      var position = Sips.indexOf(sip);

      if (0 === position)
      {
        this.el.children('#sip-body').prepend($new);
      }
      else
      {
        var $target = this.el.find('.sip').eq(position);

        if ($target.length)
        {
          $target.before($new);
        }
        else
        {
          this.el.children('#sip-body').append($new);
        }
      }

      if (0 && !this.firstPoll)
      {
        // Animation
        $new.addClass('sip-new').show('blind', {}, 500, function()
          {
            $(this).removeClass('sip-new', 2000);
          });
      }
      else
      {
        $new.show();
      }
    },

  remove: function(sip)
    {
      $(sip.view.el).hide('blind', function()
        {
          $(this).remove();
        });
    },

  updateSips: function(objects)
    {
      var itemsPerPage = 5
        , page = parseInt(getCookie(this.pagingCookie))
        , page = (isNaN(page) || page == undefined) ? 1 : page
        , itemsToSkip = (page - 1) * itemsPerPage
        , totalPages = Math.ceil(objects.length / itemsPerPage)
        , hasNextPage = page < totalPages;

      setCookie(this.pagingCookie, page, 1);

      for (i in objects)
        {
          if (i >= itemsToSkip && i < (itemsToSkip + itemsPerPage))
            {
              var sip = objects[i];

              var item = Sips.find(function(item)
                {
                  return item.get('uuid') == sip.uuid;
                });

              if (undefined === item)
                {
                  // Add new sips
                  Sips.add(sip);
                }
              else
                {
                  // Update sips
                  item.set(sip);
                  //if ($('#sip-row-' + sip.uuid).length) {
                  $('#sip-row-' + sip.uuid).parent().show();
                  //} else {
                  //  Sips.add(sip);
                  //}
                }
            }
        }

      // set up previous/next paging links
      var self = this;

      var $prev = $('<a href="#">' + gettext('Previous') + '</a>');

      $prev.click(function() {
        $('.sip').hide();
        var page = parseInt(getCookie(self.pagingCookie));
        setCookie(self.pagingCookie, page - 1, 1);
        self.updateSips(objects);
      });

      $('.grid-pager-previous-area').empty();
      if (page > 1)
        {
          $('.grid-pager-previous-area').append($prev);
        }

      var $next = $('<a href="#">' + gettext('Next') + '</a>');

      $next.click(function() {
        $('.sip').hide();
        var page = parseInt(getCookie(self.pagingCookie));
        setCookie(self.pagingCookie, page + 1, 1);
        self.updateSips(objects);
      });

      $('.grid-pager-next-area').empty();
      if (hasNextPage)
        {
          $('.grid-pager-next-area').append($next);
        }

      $('.grid-pager-summary-area').empty();
      if (totalPages > 1)
        {
          var pageDescription = '(page ' + page + ' of ' + totalPages + ')';
          $('.grid-pager-summary-area').text(pageDescription);
        }
    },

  poll: function(start)
    {
      this.firstPoll = undefined !== start;

      $.ajax({
        context: this,
        dataType: 'json',
        type: 'GET',
        url: this.statusUrl + '?' + new Date().getTime(),
        beforeSend: function()
          {
            window.statusWidget.startPoll();
          },
        error: function()
          {
            window.statusWidget.text(gettext('Error trying to connect to database. Trying again...'), true);
          },
        success: function(response)
          {
            var objects = response.objects;

            if (getURLParameter('paged'))
              {
                this.updateSips(objects);
              } else {

                for (i in objects)
                  {
                    var sip = objects[i];
                    var item = Sips.find(function(item)
                      {
                        return item.get('uuid') == sip.uuid;
                      });

                    if (undefined === item)
                      {
                        // Add new sips
                        Sips.add(sip);
                      }
                    else
                      {
                        // Update sips
                        item.set(sip);
                      }
                  }
              }

            // Delete sips
            if (Sips.length > objects.length)
            {
              var unusedSips = Sips.reject(function(sip)
                  {
                    return -1 < $.inArray(sip.get('uuid'), _.pluck(objects, 'uuid'));
                  });

              Sips.remove(unusedSips);
            }

            // MCP status
            if (response.mcp)
            {
              window.statusWidget.connect();
            }
            else
            {
              window.statusWidget.text(gettext('Error trying to connect to MCP server. Trying again...'), true);
            }
          },
        complete: function()
          {
            var self = this;

            window.statusWidget.endPoll();

            if (!self.idle)
            {
              setTimeout(function()
                {
                  self.poll();
                }, this.interval);
            }
          }
      });
    }
});
