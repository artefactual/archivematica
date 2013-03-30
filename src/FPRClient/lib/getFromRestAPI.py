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
from optparse import OptionParser
from StringIO import StringIO    
from httplib import responses
import json
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from externals import requests

def getFromRestAPI(url, params, verbose=False, auth=None):
    #url http://loacalhost
    #args {}
    #auth ('demo', 'demo')
    r = requests.get(url, params=params, auth=auth)

    if r.status_code != 200:
        print >>sys.stderr, "got error status code:", r.status_code, responses[r.status_code]
        print >>sys.stderr, "url:", url, "params:", params 
        raise Exception(r.status_code, responses[r.status_code])
    if verbose:
        print r.headers['content-type']
        print r.encoding
    
    print r
    ret = json.loads(r.content) 
    if verbose:
        for x in ret["objects"]:
            print type(x), x
    return ret['objects']

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-u",  "--url", action="store", dest="url", default="http://fprserver/api/fpr/v1/file_id/")
    parser.add_option("-p",  "--postFields", action="store", dest="postFields", default='{"format":"json", "order_by":"lastmodified", "lastmodified__gte":"2012-10-10T10:00:00"}')
    parser.add_option("-v",  "--verbose", action="store_true", dest="verbose", default=False)

    
    (opts, args) = parser.parse_args()
    getFromRestAPI(opts.url, eval(opts.postFields), verbose=opts.verbose)