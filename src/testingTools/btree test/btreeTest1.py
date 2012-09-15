#!/usr/bin/python -OO
import MySQLdb
import os
import sys



DB_CONNECTION_OPTS = dict(db="MCP", read_default_file="/etc/archivematica/archivematicaCommon/dbsettings", charset="utf8", use_unicode = True)
database=MySQLdb.connect(**DB_CONNECTION_OPTS)


sql = """SELECT currentLocation FROM %s""" % (sys.argv[1])
c=database.cursor()
c.execute(sql)
rows = c.fetchall()

foundCount= 0
for row in rows:
    basename = os.path.basename(row[0])
    dirname =  os.path.dirname(row[0])
    search = os.path.join(dirname, basename[0:len(basename)/2]).replace('%', '\%') + "%"
    sql = """SELECT fileUUID FROM %s WHERE currentLocation LIKE '%s'""" % (sys.argv[1], search)
    c=database.cursor()
    c.execute(sql)
    rows2 = c.fetchall()
    for row2 in rows2:
        foundCount+= 1
print foundCount
    

