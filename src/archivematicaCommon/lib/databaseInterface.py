#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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
# @subpackage archivematicaCommon
# @author Joseph Perry <joseph@artefactual.com>

import MySQLdb
import warnings
import os
import threading
import string
import sys
import time
from datetime import datetime

global separator
separator = "', '"
printSQL = False

#DB_CONNECTION_OPTS = dict(db="MCP", read_default_file="/etc/archivematica/archivematicaCommon/dbsettings")
DB_CONNECTION_OPTS = dict(db="MCP", read_default_file="/etc/archivematica/archivematicaCommon/dbsettings", charset="utf8", use_unicode = True)

def reconnect():
    global database
    retryAttempts = 3
    secondsBetweenRetry = 10
    for a in range(retryAttempts):
        try:
            database=MySQLdb.connect(**DB_CONNECTION_OPTS)
            database.autocommit(0)
            warnings.filterwarnings('error', category=MySQLdb.Warning)
            break
        except Exception as inst:
            print >>sys.stderr, "Error connecting to database:"
            print >>sys.stderr, type(inst)     # the exception instance
            print >>sys.stderr, inst.args
            time.sleep(secondsBetweenRetry)
            if a+1 == retryAttempts:
                raise Exception(inst)

def getSeparator():
    global separator
    return separator

def getUTCDate():
    """Returns a string of the UTC date & time in ISO format"""
    d = datetime.utcnow()
    return d.isoformat('T')

def getDeciDate(date):
    valid = "." + string.digits
    ret = ""
    for c in date:
        if c in valid:
            ret += c
        #else:
            #ret += replacementChar
    return ret


#sudo apt-get install python-mysqldb
sqlLock = threading.Lock()
sqlLock.acquire()
global database
reconnect()
sqlLock.release()

def runSQL(sql):
    global database
    if printSQL:
        print sql
    if isinstance(sql, unicode):
        sql = sql.encode('utf-8')
    #print type(sql), sql
    #found that even though it says it's compiled thread safe, running it multi-threaded crashes it.
    sqlLock.acquire()
    db = database
    try:
        #db.query(sql)
        c=database.cursor()
        c.execute(sql)
        rows = c.fetchall()
    except MySQLdb.OperationalError, message:
        #errorMessage = "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
        if message[0] == 2006 and message[1] == 'MySQL server has gone away':
            reconnect()
            sqlLock.release()
            runSQL(sql)
            return
        else:
            print >>sys.stderr, "Error with query: ", sql
            print >>sys.stderr, "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
            sqlLock.release()
            exit(-100)
    except Exception as inst:
            print >>sys.stderr, "Error query: ", sql
            print >>sys.stderr, type(inst)     # the exception instance
            print >>sys.stderr, inst.args
            sqlLock.release()
            raise Exception(inst)
    db.commit()
    sqlLock.release()
    return


def insertAndReturnID(sql):
    global database
    ret = None
    if printSQL:
        print sql
    if isinstance(sql, unicode):
        sql = sql.encode('utf-8')
    #print type(sql), sql
    #found that even though it says it's compiled thread safe, running it multi-threaded crashes it.
    sqlLock.acquire()
    db = database
    try:
        #db.query(sql)
        c=database.cursor()
        c.execute(sql)
        ret = c.lastrowid
    except MySQLdb.OperationalError, message:
        #errorMessage = "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
        if message[0] == 2006 and message[1] == 'MySQL server has gone away':
            reconnect()
            sqlLock.release()
            return insertAndReturnID(sql)
        else:
            print >>sys.stderr, "Error with query: ", sql
            print >>sys.stderr, "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
            sqlLock.release()
            exit(-100)
    except Exception as inst:
            print >>sys.stderr, "Error query: ", sql
            print >>sys.stderr, type(inst)     # the exception instance
            print >>sys.stderr, inst.args
            sqlLock.release()
            raise Exception(inst)
    db.commit()
    sqlLock.release()
    return ret



def querySQL(sql):
    global database
    if printSQL:
        print sql
    if isinstance(sql, unicode):
        sql = sql.encode('utf-8')
    sqlLock.acquire()
    try:
        c=database.cursor()
        c.execute(sql)
    except MySQLdb.OperationalError, message:
        #errorMessage = "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
        if message[0] == 2006 and message[1] == 'MySQL server has gone away':
            reconnect()
            import time
            time.sleep(10)
            c=database.cursor()
            c.execute(sql)
        else:
            print >>sys.stderr, "Error with query: ", sql
            print >>sys.stderr, "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
    except Exception as inst:
        print >>sys.stderr, "Error query: ", sql
        print >>sys.stderr, type(inst)     # the exception instance
        print >>sys.stderr, inst.args
        sqlLock.release()
        raise Exception(inst)
    return c, sqlLock
#        row = c.fetchone()
#        while row != None:
#            fileUUID = row[0]
#            filesToChecksum.append(row[0])
#            row = c.fetchone()


def queryAllSQL(sql):
    global database
    if isinstance(sql, unicode):
        sql = sql.encode('utf-8')
    if printSQL:
        print sql

    sqlLock.acquire()
    #print sql
    rows = []
    try:
        c=database.cursor()
        c.execute(sql)
        rows = c.fetchall()
        sqlLock.release()
    except MySQLdb.OperationalError, message:
        #errorMessage = "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
        if message[0] == 2006 and message[1] == 'MySQL server has gone away':
            reconnect()
            import time
            time.sleep(10)
            c=database.cursor()
            c.execute(sql)
            rows = c.fetchall()
            sqlLock.release()
        else:
            print >>sys.stderr, "Error with query: ", sql
            print >>sys.stderr, "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
            sqlLock.release()
            exit(-100)
    except Exception as inst:
        print >>sys.stderr, "Error query: ", sql
        print >>sys.stderr, type(inst)     # the exception instance
        print >>sys.stderr, inst.args
        sqlLock.release()
        raise Exception(inst)
    return rows
