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
# @subpackage MCPServer-plantUMLTextGenerator
# @author Joseph Perry <joseph@artefactual.com>

#sudo apt-get install graphviz

import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

f = open('plantUML.txt', 'w')
global processedJobChainLinks
processedJobChainLinks = []
subChains = {}
def writePlant(*items):
    p = ""
    for str in items:
        p = "%s%s" % (p, str.__str__())
    print p
    f.write(p)
    f.write("\n")

def jobChainLinkExitCodesTextGet(indent, exitCode, nextMicroServiceChainLink, exitMessage, set):
    leadIn = ""
    if set:
        leadIn = "->[false]"
    writePlant( indent, leadIn, """if "exitCodeIs %s" then""" % (exitCode.__str__()))
    if nextMicroServiceChainLink:
        jobChainLinkTextGet(indent + " ", "-->[true]", nextMicroServiceChainLink, label = "")
    else:
        writePlant(indent + " ", """-->[true] "End Of Chain" """)
   

def jobChainLinkTextGet(indent, leadIn, pk, label = ""):
    global subChains
    global processedJobChainLinks
    sql = """SELECT MicroServiceChainLinks.currentTask, MicroServiceChainLinks.defaultNextChainLink, TasksConfigs.taskType, TasksConfigs.taskTypePKReference, TasksConfigs.description, MicroServiceChainLinks.reloadFileList, Sounds.fileLocation, MicroServiceChainLinks.defaultExitMessage, MicroServiceChainLinks.microserviceGroup, StandardTasksConfigs.execute FROM MicroServiceChainLinks LEFT OUTER JOIN Sounds ON MicroServiceChainLinks.defaultPlaySound = Sounds.pk JOIN TasksConfigs on MicroServiceChainLinks.currentTask = TasksConfigs.pk LEFT OUTER JOIN StandardTasksConfigs ON TasksConfigs.taskTypePKReference = StandardTasksConfigs.pk WHERE MicroServiceChainLinks.pk = '%s';""" % (pk.__str__())
    print sql
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        currentTask = row[0]
        defaultNextChainLink = row[1]
        taskType = row[2]
        taskTypePKReference = row[3]
        description = row[4]
        reloadFileList = row[5]
        defaultSoundFile = row[6]
        defaultExitMessage = row[7]
        microserviceGroup = row[8]
        execute = row[9]
        
        if taskType == 3:
            sql = """SELECT execute FROM StandardTasksConfigs where pk = '%s'""" % (pk)
            rows = databaseInterface.queryAllSQL(sql)
            leadOut = "%d. %s" % (pk, description)
            if label != "":
                writePlant( ("%s%s \"%s %s - Assign Magic Link %s\"") % (indent, leadIn , label, leadOut, rows[0][0].__str__()) )
            else:
                writePlant( ("%s%s \"%s - Assign Magic Link %s\"") % (indent, leadIn, leadOut, rows[0][0].__str__()) )
            
            if pk in processedJobChainLinks:
                return
            else:
                processedJobChainLinks.append(pk)
        else:
            leadOut = "%d. %s" % (pk, description)
            if label != "":
                writePlant( ("%s%s \"%s %s\"") % (indent, leadIn , label, leadOut) )
            else:
                writePlant( ("%s%s \"%s\"") % (indent, leadIn, leadOut) )
            
            if pk in processedJobChainLinks:
                return
            else:
                processedJobChainLinks.append(pk)

        if taskType == 0 or taskType == 1 or taskType == 3 or taskType == 5  or taskType == 6  or taskType == 7: #|    0 | one instance |    1 | for each file                   | 
            sql = """SELECT exitCode, nextMicroServiceChainLink, exitMessage FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink = '%s';""" % (pk.__str__())
            rows2 = databaseInterface.queryAllSQL(sql)
            set = False
            ifindent = indent + " "
            for row2 in rows2:
                if set:
                    #writePlant( indent + " ", """endif""")
                    writePlant( ifindent[:-1], """else""")
                exitCode = row2[0]
                nextMicroServiceChainLink = row2[1]
                exitMessage = row2[2]
                jobChainLinkExitCodesTextGet(ifindent, exitCode, nextMicroServiceChainLink, exitMessage, set)
                set = True
                ifindent = ifindent + " "
            
            if set:
                writePlant( ifindent, """else""")
                writePlant( ifindent, """->[false] if "%d. default" then """ % (pk) )
            else:        
                writePlant( ifindent, """ if "%d. default" """ % (pk) )
                    
            if defaultNextChainLink:
                jobChainLinkTextGet(ifindent + " ", "-->[true]", defaultNextChainLink, label="")
            else:
                writePlant( ifindent, """-->[true] "End Of Chain" """ )
            while ifindent != indent + " ":
                writePlant( ifindent + " ", """endif""")
                ifindent = ifindent[:-1]
            writePlant( ifindent, """endif""" )
            
            if taskType == 6:
                subChains[execute] = None #tag the sub chain to proceed down
            
        elif taskType == 2: #
            sql = """SELECT description, chainAvailable from MicroServiceChainChoice Join MicroServiceChains ON MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk WHERE choiceAvailableAtLink = %d;""" % (pk)
            print sql
            rows2 = databaseInterface.queryAllSQL(sql)
            first = True
            ifindent = indent
            for row2 in rows2:
                leadIn = "->[false]"
                if first:
                    leadIn = ""
                    first = False
                else:
                    writePlant( ifindent[:-1], "else")
                writePlant( ifindent, leadIn, """if "select %s" then""" % (row2[0]))
                ifindent = ifindent + " "
                leadOut = "-->[true]"
                jobChainTextGet(leadOut, row2[1], indent=ifindent+" ")
        
        elif taskType == 4:
            writePlant( indent, leadIn, """ "Load Magic Link" """)
            writePlant( indent, "-->[Load Magic Link] (*)")
            

def jobChainTextGet(leadIn, pk, indent=""):
    sql = """SELECT startingLink, description FROM MicroServiceChains WHERE pk = '%s';""" % (pk.__str__())
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        startingLink = row[0]
        description = row[1]
        leadOut = "-->[" + description + " MicroServiceChain]"
        writePlant( ("%s \"%s\"") % (leadIn, description + " MicroServiceChain") )
        jobChainLinkTextGet(indent, leadOut, startingLink)


def createWatchedDirectories():
    global processedJobChainLinks
    sql = """SELECT watchedDirectoryPath, chain, expectedType FROM WatchedDirectories;"""
    rows = databaseInterface.queryAllSQL(sql)
    i = 1
    for row in rows:
        watchedDirectoryPath = row[0]
        chain = row[1]
        expectedType = row[2]
        writePlant( "@startuml WatchedDirectory-", watchedDirectoryPath.replace("%watchDirectoryPath%", "").replace("/", "_") + ".png" ) #img/activity_img10.png
        writePlant( "title " + watchedDirectoryPath )
        jobChainTextGet("(*) --> [" + watchedDirectoryPath + "]" , chain)
        writePlant( "@enduml" )
        i+=1
        
def createLoadMagic():
    global processedJobChainLinks
    sql = """SELECT TasksConfigs.description, StandardTasksConfigs.execute FROM TasksConfigs JOIN StandardTasksConfigs ON TasksConfigs.taskTypePKReference = StandardTasksConfigs.pk WHERE TasksConfigs.taskType = 3;"""
    rows = databaseInterface.queryAllSQL(sql)
    i = 1
    for row in rows:
        description = row[0]
        chainLink = row[1]
        processedJobChainLinks = []
        writePlant( "@startuml LoadMagicLink-", description, "-", chainLink ,".png" ) #img/activity_img10.png
        writePlant( "title ", description, "-", chainLink )
        jobChainLinkTextGet("", "(*) --> [" + description + "]", int(chainLink), label = "")
        writePlant( "@enduml" )
        i+=1

def createSubChains():
    global subChains
    for chain in subChains.iterkeys():
        writePlant( "@startuml SubChain-", chain.__str__() + ".png" ) #img/activity_img10.png
        writePlant( "title " + chain )
        jobChainTextGet("(*) --> [" + chain + "]" , chain)
        writePlant( "@enduml" )
    

if __name__ == '__main__':
    createWatchedDirectories()
    createLoadMagic()
    createSubChains()