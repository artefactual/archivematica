#!/usr/bin/env python

import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes

# allow "-f" to override prompt
options = sys.argv[1:]
if len(sys.argv) < 2 or not '-f' in options:
    proceed = raw_input("Are you sure you want to erase the ElasticSearch indexes? (y/N)\n")
    if proceed.lower() != 'y':
        print 'Not going to erase the indexes.'
        exit(0)

conn = pyes.ES(elasticSearchFunctions.getElasticsearchServerHostAndPort())

try:
    conn._send_request('GET', '')
except pyes.exceptions.NoServerAvailable:
    print "Connection error: Elasticsearch may not be running."
    os._exit(1)

# delete transfers ElasticSearch index
try:
    conn.delete_index('transfers')
except pyes.exceptions.IndexMissingException:
    pass

try:
    conn.delete_index('aips')
except pyes.exceptions.IndexMissingException:
    pass

print "ElasticSearch indexes deleted."
