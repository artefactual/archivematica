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
# @subpackage archivematicaClientScript
# @author Mark Jordan <mark2jordan@gmail.com>
import sys
import json
import urllib

# The base URL will be specific to each CONTENTdm server; everything including and
# following 'dmwebservices' is the same.
try:
    # Adding 1 to the dmGetCollectionList call shows hidden collections.
    # This is not documented at http://www.contentdm.org/help6/custom/customize2b.asp.
    CollectionListUrl = sys.argv[1] + '?q=dmGetCollectionList/1/json'
    f = urllib.urlopen(CollectionListUrl)
    collectionListString = f.read()
    collectionList = json.loads(collectionListString)
except:
    print "Cannot retrieve CONTENTdm collection list from " + CollectionListUrl
    sys.exit(1) 

# We only want two of the elements of each 'collection', alias and name.
cleanCollectionList = {}
for collection in collectionList:
  for k, v in collection.iteritems():
    cleanCollectionList[collection['name']] = collection['alias']


print(cleanCollectionList)
