#!/usr/bin/env python2

import MySQLdb
import warnings
import os
import threading
import sys
import time

printSQL = False
printErrors = True

#DB_CONNECTION_OPTS = dict(db="MCP", read_default_file="/etc/archivematica/archivematicaCommon/dbsettings")
DB_CONNECTION_OPTS = dict(db="MCP", read_default_file="/etc/archivematica/archivematicaCommon/dbsettings", charset="utf8", use_unicode = True)

def reconnect():
    global database
    retryAttempts = 3
    secondsBetweenRetry = 10
    for a in range(retryAttempts):
        try:
            database=MySQLdb.connect(**DB_CONNECTION_OPTS)
            database.autocommit(True)
            warnings.filterwarnings('error', category=MySQLdb.Warning)
            break
        except MySQLdb.OperationalError as inst:
            if inst[0] == 1045 and inst[1].startswith('Access denied for user'):
                raise
            else:
                print >>sys.stderr, "Error connecting to database:"
                print >>sys.stderr, type(inst)     # the exception instance
                print >>sys.stderr, inst.args
                time.sleep(secondsBetweenRetry)
                if a+1 == retryAttempts:
                    raise
        except Exception as inst:
            print >>sys.stderr, "Error connecting to database:"
            print >>sys.stderr, type(inst)     # the exception instance
            print >>sys.stderr, inst.args
            time.sleep(secondsBetweenRetry)
            if a+1 == retryAttempts:
                raise 


#sudo apt-get install python-mysqldb
sqlLock = threading.Lock()
sqlLock.acquire()
global database
reconnect()
sqlLock.release()

def runSQL(sql, arguments=None):
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
        c.execute(sql, arguments)
        database.commit()
        rows = c.fetchall()
    except MySQLdb.OperationalError as message:
        #errorMessage = "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
        if message[0] == 2006 and message[1] == 'MySQL server has gone away':
            reconnect()
            sqlLock.release()
            runSQL(sql)
            return
        else:
            if printErrors:
                print >>sys.stderr, "Error with query: ", sql
                print >>sys.stderr, "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
            sqlLock.release()
            raise 
    except Exception as inst:
        if printErrors:
            print >>sys.stderr, "Error query: ", sql
            print >>sys.stderr, type(inst)     # the exception instance
            print >>sys.stderr, inst.args
        sqlLock.release()
        raise 
    db.commit()
    sqlLock.release()
    return


def insertAndReturnID(sql, arguments=None):
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
        c.execute(sql, arguments)
        database.commit()
        ret = c.lastrowid
    except MySQLdb.OperationalError as message:
        #errorMessage = "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
        if message[0] == 2006 and message[1] == 'MySQL server has gone away':
            reconnect()
            sqlLock.release()
            return insertAndReturnID(sql)
        else:
            if printErrors:
                print >>sys.stderr, "Error with query: ", sql
                print >>sys.stderr, "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
            sqlLock.release()
            raise 
    except Exception as inst:
            print >>sys.stderr, "Error query: ", sql
            print >>sys.stderr, type(inst)     # the exception instance
            print >>sys.stderr, inst.args
            sqlLock.release()
            raise 
    db.commit()
    sqlLock.release()
    return ret



def querySQL(sql, arguments=None):
    global database
    if printSQL:
        print sql
    if isinstance(sql, unicode):
        sql = sql.encode('utf-8')
    sqlLock.acquire()
    try:
        c=database.cursor()
        c.execute(sql, arguments)
    except MySQLdb.OperationalError as message:
        #errorMessage = "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
        if message[0] == 2006 and message[1] == 'MySQL server has gone away':
            reconnect()
            import time
            time.sleep(10)
            c=database.cursor()
            c.execute(sql, arguments)
        else:
            if printErrors:
                print >>sys.stderr, "Error with query: ", sql
                print >>sys.stderr, "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
            raise 
    except Exception as inst:
        if printErrors:
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


def queryAllSQL(sql, arguments=None):
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
        c.execute(sql, arguments)
        rows = c.fetchall()
        sqlLock.release()
    except MySQLdb.OperationalError as message:
        #errorMessage = "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
        if message[0] == 2006 and message[1] == 'MySQL server has gone away':
            reconnect()
            import time
            time.sleep(10)
            c=database.cursor()
            c.execute(sql, arguments)
            rows = c.fetchall()
            sqlLock.release()
        else:
            print printErrors
            if printErrors:
                print >>sys.stderr, "Error with query: ", sql
                print >>sys.stderr, "Error %d:\n%s" % (message[ 0 ], message[ 1 ] )
            sqlLock.release()
            raise 
    except Exception as inst:
        if printErrors:
            print >>sys.stderr, "Error query: ", sql
            print >>sys.stderr, type(inst)     # the exception instance
            print >>sys.stderr, inst.args
        sqlLock.release()
        raise Exception(inst)
    return rows
