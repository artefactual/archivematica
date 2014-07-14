#!/usr/bin/python -OO

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

# @package Archivematica
# @subpackage FPRClient
# @author Joseph Perry <joseph@artefactual.com>
import ast
from optparse import OptionParser
from httplib import responses
import urlparse
import json
import requests
import sys


class FPRConnectionError(Exception):
    pass


def _get_from_rest_api(resource="", params=None, url="https://fpr.archivematica.org/fpr/api/v2/", limit=0, start_at=None, verbose=False, auth=None, verify=True):
    """
    Fetch a response from the FPR REST API.

    This is primarily an internal function used by each_record(). It is
    typically used in two ways:

    * Pass both a URL and a resource, with some parameters, in which case the
      resource will be joined to the URL before calling.
    * Pass just a URL. This is typically used when a fully-formed URL is called,
      for instance when using the preformatted "next" link provided by a
      previous API response.

    params is a dictionary of keyword arguments to be passed as the querystring.
    It should be empty if a querystring is already present in the URL.
    If no params are provided, and no querystring is present in the URL, then
    a default will be provided.

    limit controls the number of results to be returned by the server. By
    default a limit of "0" is passed, which causes the server to return the
    maximum number it supports. (For current versions of the FPR server, this
    is 1000. It does *not* return all results.)

    start_at is a date; it can be used to filter results and only return
    rules newer than a certain date. This is usually used to ensure that
    FPR pulls bring in only rules newer than the newest rule in the
    local database.

    verbose, when passed as True, causes verbose information about the request
    to be printed at the conclusion of the request.

    auth allows an auth tuple of (username, password) to be passed. They will
    be used to perform HTTP basic authentication, if present.

    verify controls whether or not the SSL certificate of the FPR server
    should be checked. This is on by default, but can be disabled to connect
    to test FPR servers which may not have valid SSL certificates.
    """
    # TOOD make this use slumber
    # How to dynamically set resource in api.resource.get()
    parsed_url = urlparse.urlparse(url)

    # Don't make any modifications to existing querystring
    if parsed_url.query:
        params = {}
    # supply default format, as FPR requires "format=json" to be specified
    elif not params:
        params = {
            "format": "json"
        }

    if start_at:
        params["order_by"] = "lastmodified"
        params['lastmodified__gte'] = start_at

    if limit:
        params["limit"] = limit

    resource_url = urlparse.urljoin(url, resource)
    r = requests.get(resource_url, params=params, auth=auth, timeout=10, verify=verify)

    if r.status_code != 200:
        print >>sys.stderr, "got error status code:", r.status_code, responses[r.status_code]
        print >>sys.stderr, "resource_url:", resource_url, "params:", params
        raise FPRConnectionError(r.status_code, responses[r.status_code])
    if verbose:
        print r
        print r.headers['content-type']
        print r.encoding

    ret = json.loads(r.content)
    if verbose:
        for x in ret["objects"]:
            print x
    return ret


def each_record(resource, url="https://fpr.archivematica.org/fpr/api/v2/", start_at=None, verify=True, verbose=False):
    """
    Iterate over every FPR record for a given resource.

    "resource" should be the FPR server's name for the given category
    of FPR rule. For instance, "fp-tool".

    url is the base URL of the FPR server. If not provided, Artefactual's
    production FPR server will be used.

    start_at is a date; it can be used to filter results and only return
    rules newer than a certain date. This is usually used to ensure that
    FPR pulls bring in only rules newer than the newest rule in the
    local database.

    verify controls whether or not the SSL certificate of the FPR server
    should be checked. This is on by default, but can be disabled to connect
    to test FPR servers which may not have valid SSL certificates.

    verbose, when passed as True, causes verbose information about the request
    to be printed at the conclusion of the request.
    """
    url = urlparse.urlparse(url)
    base_url = "{}://{}".format(url.scheme, url.netloc)

    response = _get_from_rest_api(resource, url=url.geturl(),
                                  start_at=start_at, limit=100,
                                  verify=verify, verbose=verbose)

    for object in response["objects"]:
        yield object

    while response["meta"]["next"]:
        next = urlparse.urljoin(base_url, response["meta"]["next"])
        response = _get_from_rest_api(url=next, verify=verify)

        for object in response["objects"]:
            yield object

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-u", "--url", action="store", dest="url", default="https://fpr.archivematica.org/fpr/api/v2/")
    parser.add_option('-r', '--resource', action='store', dest='resource')
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False)

    (opts, args) = parser.parse_args()
    for record in each_record(opts.resource, opts.url, verbose=opts.verbose):
        pass
