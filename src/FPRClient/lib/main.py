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
import uuid
from addLinks import addLinks
from optparse import OptionParser
from getFromRestAPI import getFromRestAPI
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

databaseInterface.printSQL = True


def create(table, entry):
    global maxLastUpdate
    sets = []
    for key, value in entry.iteritems():
        if key == "resource_uri":
            continue
        if key == "uuid":
            key = "pk"
        if key == "lastmodified" and value > maxLastUpdate:
            maxLastUpdate = value
        #print type(value)
        if value == None:
            sets.append("%s=NULL" % (key))
        elif isinstance(value, int):
            sets.append("%s=%s" % (key, value))
        elif isinstance(value, unicode):
            sets.append("%s='%s'" % (key, databaseInterface.MySQLdb.escape_string(value)))
        elif isinstance(value, str):
            sets.append("%s='%s'" % (key, databaseInterface.MySQLdb.escape_string(value)))
            
    sets = ", ".join(sets)
    sql = """INSERT INTO %s SET %s;""" % (table, sets)
    #print sql
    databaseInterface.runSQL(sql)
    
             

def getMaxLastUpdate():
    sql = """SELECT variableValue FROM UnitVariables WHERE unitType = 'FPR' AND unitUUID = 'Client' AND variable = 'maxLastUpdate' """
    rows = databaseInterface.queryAllSQL(sql)
    if rows:
        maxLastUpdate = rows[0][0]
    else:
        maxLastUpdate = "2000-01-01T00:00:00"
    return maxLastUpdate

def setMaxLastUpdate(maxLastUpdate):
    sql = """SELECT pk FROM UnitVariables WHERE unitType = 'FPR' AND unitUUID = 'Client' AND variable = 'maxLastUpdate'; """
    rows = databaseInterface.queryAllSQL(sql)
    if rows:
        sql = """UPDATE UnitVariables SET variableValue='%s' WHERE unitType = 'FPR' AND unitUUID = 'Client' AND variable = 'maxLastUpdate';""" % (maxLastUpdate)
        databaseInterface.runSQL(sql)
    else:
        pk = uuid.uuid4().__str__()
        sql = """INSERT INTO UnitVariables SET pk='%s', variableValue='%s', unitType='FPR', unitUUID = 'Client', variable = 'maxLastUpdate';""" % (pk, maxLastUpdate)
        databaseInterface.runSQL(sql)
    return maxLastUpdate


if __name__ == '__main__':
    global maxLastUpdate
    maxLastUpdate = getMaxLastUpdate()
    maxLastUpdateAtStart = maxLastUpdate
    databaseInterface.runSQL("SET foreign_key_checks = 0;")
    server = "http://fpr.archivematica.org:8000"
    for x in [
        ("CommandRelationships", server + "/fpr/api/v1/CommandRelationship/"),
        ("FileIDsBySingleID", server + "/fpr/api/v1/FileIDsBySingleID/"),
        ("FileIDs", server + "/fpr/api/v1/FileID/"),
        ("Commands", server + "/fpr/api/v1/Command/"),
        ("CommandTypes", server + "/fpr/api/v1/CommandType/"),
        ("CommandClassifications", server + "/fpr/api/v1/CommandClassification/"),
        ("CommandsSupportedBy", server + "/fpr/api/v1/CommandsSupportedBy/"),
        ("FileIDTypes", server + "/fpr/api/v1/FileIDType/"),
        ("Groups", server + "/fpr/api/v1/Group/"),
        ("FileIDGroupMembers", server + "/fpr/api/v1/FileIDGroupMember/"),
        ("SubGroups", server + "/fpr/api/v1/SubGroup/"),
        ("DefaultCommandsForClassifications", server + "/fpr/api/v1/DefaultCommandsForClassification/")
    ]:
        table, url = x
        #params = {"format":"json", "order_by":"lastmodified", "lastmodified__gte":maxLastUpdateAtStart, "limit":"0"}
        params = {"format":"json", "order_by":"lastmodified", "lastmodified__gte":maxLastUpdateAtStart, "limit":"0"}
        entries = getFromRestAPI(url, params, verbose=False, auth=None)
        #print "test", entries
        for entry in entries:
            #print table, entry
            
            #check if it already exists
            sql = """SELECT pk FROM %s WHERE pk = '%s'""" % (table, entry['uuid'])
            if databaseInterface.queryAllSQL(sql):
                #pass
                continue
            
            if not 'replaces' in entry:
                print >>sys.stderr, "Required entry 'replaces' missing."
                print entry
                #continue
                exit(3)
                
            #If updating a disabled entry, it will continue to be disabled.
            if entry['replaces'] != None:
                 sql = """SELECT enabled FROM %s WHERE pk = '%s';""" % (table, entry['replaces'])
                 enabled=databaseInterface.queryAllSQL(sql)[0][0]
                 if not enabled:
                     entry['enabled'] = 0
                 sql = """UPDATE %s SET enabled=FALSE WHERE pk = '%s';""" % (table, entry['replaces'])
                 databaseInterface.runSQL(sql)
                 
            create(table, entry) 
            
    #createLinks()
    addLinks()
    databaseInterface.runSQL("SET foreign_key_checks = 1;")
    if maxLastUpdate != maxLastUpdateAtStart:
        setMaxLastUpdate(maxLastUpdate)
    print maxLastUpdate