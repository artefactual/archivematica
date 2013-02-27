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
from getFromRestAPI import getFromRestAPI
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

def create(table, entry):
    sets = []
    for key, value in entry.iteritems():
        if key == "resource_uri":
            continue
        if key == "uuid":
            key = "pk"
        #print type(value)
        if isinstance(key, str):
            sets.append("%s='%s'" % (key, value))
        elif isinstance(key, unicode):
            sets.append("%s='%s'" % (key, value))
        elif isinstance(key, int):
            sets.append("%s=%s" % (key, value))
        elif value == None:
            sets.append("%s=NULL" % (key))
    sets = ", ".join(sets)
    sql = """INSERT INTO %s SET %s;""" % (table, sets)
    print sql
    #databaseInterface.runSQL(sql)
             




if __name__ == '__main__':
    for x in [
        ("CommandRelationships", "http://fprserver/api/fpr/v1/FPRFileIDs/"),
        ("FileIDsBySingleID", "http://fprserver/api/fpr/v1/FPRFileIDsBySingleID/"),
        ("FileIDs", "http://fprserver/api/fpr/v1/FPRFileIDs/"),
        ("Commands", "http://fprserver/api/fpr/v1/FPRCommands/")
    ]:
        table, url = x
        params = {"format":"json", "order_by":"lastmodified", "lastmodified__gte":"2012-10-10T10:00:00", "limit":"0"}
        entries = getFromRestAPI(url, params, verbose=False, auth=None)
        #print "test", entries
        for entry in entries:
            #print table, entry
            
            #check if it already exists
            sql = """SELECT pk FROM %s WHERE pk = '%s'""" % (table, entry['uuid'])
            if databaseInterface.queryAllSQL(sql):
                continue
            create(table, entry) 
            
            #if replaces:
            #    updatefk()
            
            #if removeReplacement:
            #    todo()
                
            
    #createLinks()
    #update last modified time
    
    