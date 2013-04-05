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

var NotificationView = Backbone.View.extend({
  initialize: function() {
    this.initializeLocalData();
    var notificationData = this.getNotificationData();
    this.currentId = notificationData.currentId;
    this.displayed = [];
  },

  initializeLocalData: function() {
    // initialize local storage
    if (localStorage.getItem('archivematicaNotifications') == null)
    {
       localStorage.setItem('archivematicaNotifications', JSON.stringify({
         'notifications': [],
         'dismissed': [],
         'currentId': 0
       }));
    }
  },

  add: function(notification)
  {
    this.currentId = this.currentId + 1;
    notification.id = this.currentId;
    var localNotificationData = this.getNotificationData();
    localNotificationData.currentId = this.currentId;
    localNotificationData.notifications.push(notification);
    this.setNotificationData(localNotificationData);
  },

  getNotificationData: function() {
    return JSON.parse(localStorage.getItem('archivematicaNotifications'));
  },

  setNotificationData: function(notificationData) {
    localStorage.setItem('archivematicaNotifications', JSON.stringify(notificationData));
  },

  render: function() {
    // get currently stored notifications
    var localNotificationData = JSON.parse(localStorage.getItem('archivematicaNotifications'));

    if (localNotificationData != null)
    {
      // cycle through notifications
      for(var index in localNotificationData.notifications) {
        var notification = localNotificationData.notifications[index];

        // if notification hasn't been displayed on this page yet, display it
        if (this.displayed.indexOf(notification.id) == -1)
        {
          var $notificationDiv = $('<div class="alert-message"></div>');

          $notificationDiv
            .html(notification.message)
            .click(function() {
              // fade out notification
              $(this).fadeOut();

              // delete notification from localStorage

              // load notifications
              var localNotificationData = JSON.parse(localStorage.getItem('archivematicaNotifications'))
                , revisedNotifications = [];

              // remove the one that was clicked on
              for(var index in localNotificationData.notifications) {
                var compareNotification = localNotificationData.notifications[index];
                if (notification.id != compareNotification.id)
                {
                  revisedNotifications.push(compareNotification);
                }
              }

              // store revised notifications
              localNotificationData.notifications = revisedNotifications;
              localStorage.setItem('archivematicaNotifications', JSON.stringify(localNotificationData));
            });

          $(this.el).append($notificationDiv);

          // note that it has been displayed on the page
          this.displayed.push(notification.id);
        }
      }
    }

    // refresh notifications each second
    var self = this;
    setTimeout(function() {
      self.render();
    }, 1000);
  }
});

Date.prototype.getArchivematicaDateTime = function()
  {
    return this.getArchivematicaDateString();
  };

Date.prototype.getArchivematicaDateString = function()
  {
    var pad = function (n)
      {
        return n < 10 ? '0' + n : n;
      }

    var dateText = this.getFullYear()
      + '-' + pad(this.getMonth() + 1)
      + '-' + pad(this.getDate())
      + ' ' + pad(this.getHours())
      + ':' + pad(this.getMinutes());

    if (dateText == 'NaN-NaN-NaN NaN:NaN') {
      dateText = '';
    }

    return dateText;
  };

function localizeTimestampElements() {
  $('.timestamp').each(function() {
    $(this).text(timestampToLocal($(this).text()));
  });
}

function timestampToLocal(timestamp) {
  // convert to milliseconds
  var date = new Date(timestamp * 1000);

  return date.getArchivematicaDateString();
}

function setCookie(c_name, value, exdays) {
  var exdate=new Date();
  exdate.setDate(exdate.getDate() + exdays);
  var c_value=escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
  document.cookie=c_name + "=" + c_value;
}

function getCookie(c_name) {
  var i,x,y,ARRcookies=document.cookie.split(";");
  for (i=0;i<ARRcookies.length;i++) {
    x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
    y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
    x=x.replace(/^\s+|\s+$/g,"");
    if (x==c_name) {
      return unescape(y);
    }
  }
}

function getURLParameter(name) {
  var value = decodeURI(
    (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
  );
  return (value == 'null') ? false : value;
}

function reloadPageableElement(destinationDomElement, url, page) {
  $.ajax({
    type: 'GET',
    cache: false,
    data: {
      'page': page
    },
    success: function(data)
      {
        $(destinationDomElement).html(data);
        localizeTimestampElements();
      },
    url: url
  });
}

$(document).ready(
  function()
    {
      $('.preview-help-text')

        // Preview text
        .children('.preview')
          .show()
          .children('a')
            .click(function(event)
              {
                event.preventDefault();
                $(this).closest('.preview').hide();
                $(this).closest('.preview-help-text').children('.content').show();
              })
          .end()
        .end()

        // Content
        .children('.content')
          .hide()
          .append(' <a href="#">(collapse)</a>')
          .children('a')
            .click(function(event)
              {
                event.preventDefault();
                $(this).closest('.content').hide();
                $(this).closest('.preview-help-text').children('.preview').show();
              });
    });
