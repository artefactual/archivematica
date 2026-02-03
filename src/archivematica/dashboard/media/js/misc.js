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

// Converts a Unix timestamp in seconds to a local datetime string formatted as
// "YYYY-MM-DD HH:mm".
// TODO: use Intl.DateTimeFormat instead of manual formatting.
function timestampToLocal(timestamp) {
  var date = new Date(timestamp * 1000);
  if (Number.isNaN(date.getTime())) {
    return '';
  }

  const pad = (n) => String(n).padStart(2, '0');

  const datePart = [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate())
  ].join('-');

  const timePart = [
    pad(date.getHours()),
    pad(date.getMinutes())
  ].join(':');

  return `${datePart} ${timePart}`;
}

// Converts an ISO datetime string to a localized date-time string.
function datetimeToLocal(dt) {
  var date = new Date(dt);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return date.toLocaleString();
}

// Localizes the text of .timestamp and .datetime elements.
function localizeTimestampElements() {
  $('.timestamp').each(function() {
    const $el = $(this);
    $el.text(timestampToLocal($el.text()));
  });

  $('.datetime').each(function() {
    const $el = $(this);
    $el.text(datetimeToLocal($el.text()));
  });
}

// Returns the value of the cookie with the given name, or undefined.
function getCookie(name) {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [key, ...rest] = cookie.split('=');
    if (key.trim() === name) {
      return decodeURIComponent(rest.join('='));
    }
  }

  return undefined;
}
