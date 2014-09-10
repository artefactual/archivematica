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

$(function() {
  // add job viewer to generate dialogs with
  var job = new Job();
  job.set({'type': 'Approve Normalization'});
  job.sip = new Sip();
  job.sip.set({'directory': '{{ sipname }}'});
  var jobView = new BaseJobView({model: job});

  // add popovers
  $($.find('a.file-location'))
    .popover({
      trigger: 'hover',
      content: function()
        {
            return $(this).attr('data-location').replace(/%.*%/gi, '');
        }
    })
    .click(function(event) {
      event.preventDefault();
    });
});
