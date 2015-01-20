#!/usr/bin/env python

import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from elasticSearchFunctions import getElasticsearchServerHostAndPort

from elasticsearch import Elasticsearch, ConnectionError, TransportError

# allow "-f" to override prompt
options = sys.argv[1:]
if len(sys.argv) < 2 or not '-f' in options:
    proceed = raw_input("Are you sure you want to erase the ElasticSearch indexes? (y/N)\n")
    if proceed.lower() != 'y':
        print 'Not going to erase the indexes.'
        sys.exit(0)

conn = Elasticsearch(hosts=getElasticsearchServerHostAndPort())
try:
    conn.info()
except ConnectionError, TransportError:
    print "Connection error: Elasticsearch may not be running."
    sys.exit(1)

# delete transfers ElasticSearch index
# Ignore 404, in case the index is missing (e.g. already deleted)
conn.indices.delete('transfers', ignore=404)
conn.indices.delete('aips', ignore=404)

print "ElasticSearch indexes deleted."
