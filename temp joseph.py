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
# @subpackage transcoder
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import uuid
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import traceback

#used to control testing of an individual call to databaseInterface.runSQL() 
def runSQL(sql):
    if True:
        databaseInterface.runSQL(sql)


tables = ['CommandsSupportedBy', 'FileIDs', 'FileIDsByExtension', 'CommandClassifications', 'CommandTypes', 'Commands', 'CommandRelationships', 'DefaultCommandsForClassifications']

sql = """
        select 
        concat(table_name, '.', column_name) as 'foreign key',  
        concat(referenced_table_name, '.', referenced_column_name) as 'references',
        table_name,
        column_name,
        referenced_table_name,
        referenced_column_name,
        CONSTRAINT_NAME
    from
        information_schema.key_column_usage
    where
        referenced_table_name is not null
    AND(
        referenced_table_name = 'CommandsSupportedBy' OR 
        referenced_table_name = 'FileIDs' OR 
        referenced_table_name = 'FileIDsByExtension' OR 
        referenced_table_name = 'CommandClassifications' OR 
        referenced_table_name = 'CommandTypes' OR 
        referenced_table_name = 'Commands' OR 
        referenced_table_name = 'CommandRelationships' OR 
        referenced_table_name = 'DefaultCommandsForClassifications'
    ) GROUP BY concat(table_name, '.', column_name)
    ORDER BY  concat(table_name, '.', column_name);"""
rowsRelationships = databaseInterface.queryAllSQL(sql)


def part1():
    #Create new pk columns and assign them random UUIDs
    for table in tables:
        sql = "ALTER TABLE %s  ADD newPK VARCHAR(50);" % (table)
        runSQL(sql)
        sql = "SELECT pk from %s" % (table)
        rows = databaseInterface.queryAllSQL(sql)
        for row in rows:
            UUID = uuid.uuid4().__str__()
            sql = "UPDATE %s SET newPK='%s' WHERE pk = %d;" % (table, UUID, row[0])
            runSQL(sql)
    
    #Create new foreign key columns and populate them with the appropriate UUID's
    for row in rowsRelationships:
        #print >>sys.stderr, "\n", row[0], " -> ",  row[1]
        table_name = row[2]
        column_name = row[3]
        referenced_table_name = row[4]
        referenced_column_name = row[5]
        constraint_name = row[6]
        
        try:
            runSQL("ALTER TABLE %s ADD %s_new VARCHAR(50)" % (table_name, column_name) )
            
            sql = "SELECT pk, newPK from %s" % (referenced_table_name)
            rows2 = databaseInterface.queryAllSQL(sql)
            for row2 in rows2:
                pk, newPK = row2
                runSQL("UPDATE %s SET %s='%s' WHERE %s = %d;" % (table_name, column_name+"_new", newPK, column_name, pk ))
            
            #http://lists.mysql.com/mysql/204199
            try:
                #print "trying part 2"
                sql = "ALTER TABLE %s DROP FOREIGN KEY %s;" % (table_name, constraint_name) 
                runSQL(sql)
                #databaseInterface.runSQL(sql)
            except:
                print >>sys.stderr, "except 2"
            
            try:
                #print "trying part 3"
                sql = "ALTER TABLE %s DROP COLUMN %s;" % (table_name, column_name)
                runSQL(sql)
                #databaseInterface.runSQL(sql)
            except:
                print >>sys.stderr, "except 3"
                
        except Exception as inst:
            traceback.print_exc(file=sys.stdout)
            print >>sys.stderr, "DEBUG EXCEPTION!"
            print >>sys.stderr, type(inst)     # the exception instance
            print >>sys.stderr, inst.args
            continue
        
        
    
    #Set the pk as the new pk, and 
    for table in tables:
        runSQL( "ALTER TABLE %s CHANGE pk pk INT;" % (table) )
        runSQL( "ALTER TABLE %s DROP PRIMARY KEY;" % (table) )
        runSQL( "ALTER TABLE %s ADD PRIMARY KEY (newPK);" % (table) )
        runSQL( "ALTER TABLE %s DROP COLUMN pk;" % (table) )
        runSQL( "ALTER TABLE %s CHANGE newPK pk VARCHAR(50) FIRST;" % (table) )
        runSQL( "ALTER TABLE %s ADD INDEX %s(pk);" % (table, table) )
        
    
        
def part2():    
    #rename the fk_new to fk
    #set the fk relationship    
    for row in rowsRelationships:
        print >>sys.stderr, "\n", row[0], " -> ",  row[1]
        table_name = row[2]
        column_name = row[3]
        referenced_table_name = row[4]
        referenced_column_name = row[5]
        constraint_name = row[6]
        try:
            runSQL( "ALTER TABLE %s  CHANGE %s_new %s VARCHAR(50) AFTER pk;" % (table_name, column_name, column_name) )
            print >>sys.stderr, "renamed"
        except Exception as inst:
            traceback.print_exc(file=sys.stdout)
            print >>sys.stderr, "DEBUG EXCEPTION!"
        try:
            runSQL( "ALTER TABLE %s ADD FOREIGN KEY (%s) REFERENCES %s(%s)" %(table_name, column_name, referenced_table_name, referenced_column_name) )
            print >>sys.stderr, "added fk"
        except Exception as inst:
            traceback.print_exc(file=sys.stdout)
            print >>sys.stderr, "DEBUG EXCEPTION!"

if __name__ == '__main__':
    part1()
    part2()
    
#SHOW CREATE TABLE CommandRelationships;
    
    

