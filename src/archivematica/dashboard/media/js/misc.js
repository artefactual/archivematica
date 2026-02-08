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

function timestampToLocal(timestamp) {
  // convert to milliseconds
  'use strict';
  var date = new Date(timestamp * 1000);

  return date.getArchivematicaDateString();
}

function datetimeToLocal(dt) {
  // Converts an ISO formatted string to localtime
  'use strict';
  var date = new Date(dt);
  return date.toLocaleString();
}

function localizeTimestampElements() {
  'use strict';
  $('.timestamp').each(function() {
    $(this).text(timestampToLocal($(this).text()));
  });
  $('.datetime').each(function() {
    $(this).text(datetimeToLocal($(this).text()));
  });
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
