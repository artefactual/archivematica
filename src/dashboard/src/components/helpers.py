# -*- coding: utf-8 -*-
# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import

import json
import logging
import mimetypes
import os
import pprint
import requests
from wsgiref.util import FileWrapper

from django.conf import settings as django_settings
from django.utils.dateformat import format
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.urls import reverse
from django.db import connection
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.utils.translation import ugettext as _
from tastypie.models import ApiKey
from six.moves.urllib.parse import urlencode, urljoin
from six.moves import range
from six.moves import zip

from amclient import AMClient

from main import models


logger = logging.getLogger("archivematica.dashboard")


class AtomError(Exception):
    pass


# Used for debugging


def pr(object):
    return pprint.pformat(object)


# Used for raw SQL queries to return data in dictionaries instead of lists


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [dict(list(zip([col[0] for col in desc], row))) for row in cursor.fetchall()]


def keynat(string):
    r"""A natural sort helper function for sort() and sorted()
    without using regular expressions or exceptions.

    >>> items = ('Z', 'a', '10th', '1st', '9')
    >>> sorted(items)
    ['10th', '1st', '9', 'Z', 'a']
    >>> sorted(items, key=keynat)
    ['1st', '9', '10th', 'a', 'Z']
    """
    it = type(1)
    r = []
    for c in string:
        if c.isdigit():
            d = int(c)
            if r and isinstance(r[-1], it):
                r[-1] = r[-1] * 10 + d
            else:
                r.append(d)
        else:
            r.append(c.lower())
    return r


def json_response(data, status_code=200):
    return HttpResponse(
        json.dumps(data), content_type="application/json", status=status_code
    )


def pager(objects, items_per_page, current_page_number):
    """

    :param objects: Iterable of items to paginate
    :param items_per_page: Number of items on each page
    :param current_page_number: Page to return information for
    :return: django.paginator.Page object (with additional attributes)
    """
    if current_page_number is None:
        current_page_number = 1

    paginator = Paginator(objects, items_per_page)
    try:
        page = paginator.page(current_page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page = paginator.page(paginator.num_pages)

    # For compatibility with old code, add the alternate names as attributes
    # TODO replace all places that call this with the actual parameters
    page.objects = page.object_list
    page.current = page.number
    try:
        page.previous = page.previous_page_number()
    except InvalidPage:
        page.previous = None
    try:
        page.next = page.next_page_number()
    except InvalidPage:
        page.next = None
    page.has_other = page.has_other_pages()
    page.total_items = paginator.count
    page.num_pages = paginator.num_pages

    # Add lists of the (up to) 5 adjacent pages
    num_neighbours = 5
    if page.number > num_neighbours:
        page.previous_pages = list(range(page.number - num_neighbours, page.number))
    else:
        page.previous_pages = list(range(1, page.number))

    if page.number < (paginator.num_pages - num_neighbours):
        page.next_pages = list(range(page.number + 1, page.number + num_neighbours + 1))
    else:
        page.next_pages = list(range(page.number + 1, paginator.num_pages + 1))

    return page


def task_duration_in_seconds(task):
    if task.endtime is not None:
        duration = int(format(task.endtime, "U")) - int(format(task.starttime, "U"))
    else:
        duration = ""
    if duration == 0:
        duration = "< 1"
    return duration


def get_metadata_type_id_by_description(description):
    return models.MetadataAppliesToType.objects.get(description=description)


def get_setting(setting, default=""):
    try:
        setting = models.DashboardSetting.objects.get(name=setting)
        return setting.value
    except:
        return default


def get_boolean_setting(setting, default=""):
    setting = get_setting(setting, default)
    if setting == "False":
        return False
    else:
        return bool(setting)


def set_setting(setting, value=""):
    try:
        setting_data = models.DashboardSetting.objects.get(name=setting)
    except:
        setting_data = models.DashboardSetting.objects.create()
        setting_data.name = setting
    # ``DashboardSetting.value`` is a string-based field. The empty string is
    # the way to represent the lack of data, therefore NULL values are avoided.
    if value is None:
        value = ""
    setting_data.value = value
    setting_data.save()


def get_atom_levels_of_description(clear=True):
    """
    Fetch levels of description from an AtoM instance and store them in the database.
    The URL and authentication details for the AtoM instance must already be stored in the settings.
    Note that only English levels of description are fetched at this point in time.

    :param bool clear: When True, deletes all existing levels of description from the Archivematica database before fetching; otherwise, the fetched levels of description will be appended to the already-stored values.
    :raises AtomError: if no AtoM URL or authentication credentials are defined in the settings, or if the levels of description cannot be fetched for another reason
    """
    settings = models.DashboardSetting.objects.get_dict("upload-qubit_v0.0")

    url = settings.get("url")
    if not url:
        raise AtomError(_("AtoM URL not defined!"))

    email = settings.get("email")
    password = settings.get("password")
    if not email or not password:
        raise AtomError(_("AtoM authentication settings not defined!"))
    auth = (email, password)

    # taxonomy 34 is "level of description"
    dest = urljoin(url, "api/taxonomies/34")
    response = requests.get(
        dest,
        params={"culture": "en"},
        auth=auth,
        timeout=django_settings.AGENTARCHIVES_CLIENT_TIMEOUT,
    )
    if response.status_code == 200:
        base = 1
        if clear:
            models.LevelOfDescription.objects.all().delete()
        else:
            # Add after existing LoD
            base = (
                models.LevelOfDescription.objects.aggregate(max=Max("sortorder"))["max"]
                + 1
            )
        levels = response.json()
        for idx, level in enumerate(levels):
            lod = models.LevelOfDescription(name=level["name"], sortorder=base + idx)
            lod.save()
    else:
        raise AtomError(_("Unable to fetch levels of description from AtoM!"))


def redirect_with_get_params(url_name, *args, **kwargs):
    url = reverse(url_name, args=args)
    params = urlencode(kwargs)
    return HttpResponseRedirect(url + "?%s" % params)


def send_file(request, filepath, force_download=False):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    filename = os.path.basename(filepath)
    extension = os.path.splitext(filepath)[1].lower()

    wrapper = FileWrapper(open(filepath))
    response = HttpResponse(wrapper)

    # force download for certain filetypes
    extensions_to_download = [".7z", ".zip"]

    if force_download or (extension in extensions_to_download):
        response["Content-Type"] = "application/force-download"
        response["Content-Disposition"] = 'attachment; filename="' + filename + '"'
    else:
        response["Content-type"] = mimetypes.guess_type(filename)[0]

    response["Content-Length"] = os.path.getsize(filepath)
    return response


def file_is_an_archive(file):
    file = file.lower()
    return file.endswith(".zip") or file.endswith(".tgz") or file.endswith(".tar.gz")


def pad_destination_filepath_if_it_already_exists(filepath, original=None, attempt=0):
    if original is None:
        original = filepath
    attempt = attempt + 1
    if os.path.exists(filepath):
        if os.path.isdir(filepath):
            return pad_destination_filepath_if_it_already_exists(
                original + "_" + str(attempt), original, attempt
            )
        else:
            # need to work out basename
            basedirectory = os.path.dirname(original)
            basename = os.path.basename(original)
            # do more complex padding to preserve file extension
            period_position = basename.index(".")
            non_extension = basename[0:period_position]
            extension = basename[period_position:]
            new_basename = non_extension + "_" + str(attempt) + extension
            new_filepath = os.path.join(basedirectory, new_basename)
            return pad_destination_filepath_if_it_already_exists(
                new_filepath, original, attempt
            )
    return filepath


def processing_config_path():
    return os.path.join(
        django_settings.SHARED_DIRECTORY,
        "sharedMicroServiceTasksConfigs/processingMCPConfigs",
    )


def _prepare_stream_response(
    payload, content_type, content_disposition, preview_file=False
):
    """Prepare the streaming response to return to the caller."""
    if preview_file:
        content_disposition = "inline"
    response = StreamingHttpResponse(payload)
    response["Content-Type"] = content_type
    response["Content-Disposition"] = content_disposition
    return response


def stream_mets_from_storage_service(
    transfer_name, sip_uuid, error_message="Unexpected error: {}"
):
    """Enable the streaming of an individual AIP METS file from the Storage
    Service.
    """
    absolute_transfer_name = "{}-{}".format(transfer_name, sip_uuid)
    mets_name = "METS.{}.xml".format(sip_uuid)
    mets_path = "{}/data/{}".format(absolute_transfer_name, mets_name)
    # We can't get a lot of debug information from AMClient yet, so we try to
    # download and then open, returning an error if the file can't be accessed.
    try:
        response = AMClient(
            ss_api_key=get_setting("storage_service_apikey", None),
            ss_user_name=get_setting("storage_service_user", "test"),
            ss_url=get_setting("storage_service_url", None).rstrip("/"),
            package_uuid=sip_uuid,
            relative_path=mets_path,
            stream=True,
        ).extract_file()
    except requests.exceptions.ConnectionError as err:
        err_response = {"success": False, "message": error_message.format(err)}
        return json_response(err_response, status_code=503)
    if response.status_code != 200:
        err_response = {
            "success": False,
            "message": error_message.format(response.content),
        }
        return json_response(err_response, status_code=response.status_code)
    content_type = "application/xml"
    content_disposition = "attachment; filename={};".format(mets_name)
    return _prepare_stream_response(
        payload=response,
        content_type=content_type,
        content_disposition=content_disposition,
    )


def stream_file_from_storage_service(
    url, error_message="Remote URL returned {}", preview_file=False
):
    # Repetetive or constant values to use below when seeting the headers.
    storage_timeout = django_settings.STORAGE_SERVICE_CLIENT_TIMEOUT
    stream = requests.get(url, stream=True, timeout=storage_timeout)
    if stream.status_code != 200:
        response = {
            "success": False,
            "message": error_message.format(stream.status_code),
        }
        return json_response(response, status_code=400)
    content_type = stream.headers.get("content-type", "text/plain")
    content_disposition = stream.headers.get("content-disposition")
    return _prepare_stream_response(
        payload=stream,
        content_type=content_type,
        content_disposition=content_disposition,
        preview_file=preview_file,
    )


def completed_units_efficient(unit_type="transfer", include_failed=True):
    """Returns a list of unit UUIDs corresponding to the non-hidden completed
    units. Uses a single database request. If ``include_failed`` is ``True``,
    failed units will be included in the returned list. Note that the criteria
    used here for determining that a unit is completed (and failed) are
    intended to coincide exactly with the criteria used by
    api/views.py::get_unit_status
    """
    table_name = "Transfers"
    pk_name = "transferUUID"
    if unit_type != "transfer":
        table_name = "SIPs"
        pk_name = "sipUUID"
    q = (
        "SELECT u.{pk_name}, j.jobType, j.microserviceGroup"
        " FROM {table_name} as u"
        " INNER JOIN Jobs as j"
        " ON j.SIPUUID = u.{pk_name}"
        " WHERE u.hidden = 0"
        " ORDER BY u.{pk_name}, j.createdTime DESC, j.createdTimeDec DESC;".format(
            table_name=table_name, pk_name=pk_name
        )
    )
    completed = set()
    current_uuid = None
    with connection.cursor() as cursor:
        cursor.execute(q)
        for uuid, job_type, ms_group in cursor.fetchall():
            if uuid == current_uuid:
                first = False
            else:
                first = True
            current_uuid = uuid
            if (
                job_type
                in ("Create SIP from transfer objects", "Move transfer to backlog")
            ) or (
                first
                and (
                    job_type == "Remove the processing directory"
                    or "failed" in ms_group.lower()
                )
            ):
                completed.add(uuid)
    return list(completed)


def generate_api_key(user):
    """
    Generate API key for a user
    """
    api_key, _ = ApiKey.objects.get_or_create(user=user)
    api_key.key = api_key.generate_key()
    api_key.save()


def get_api_allowlist():
    """Get API allowlist setting."""
    return get_setting("api_whitelist", "")


def set_api_allowlist(allowlist):
    """Set API allowlist setting.

    ``allowlist`` (str) is a space-separated list of IP addresses with access
    to the public API. If falsy, all clients are allowed.
    """
    if not allowlist:
        allowlist = ""
    return set_setting("api_whitelist", allowlist)
