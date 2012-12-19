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
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>

#sudo apt-get install python-pygraphviz
#http://networkx.lanl.gov/pygraphviz/

import traceback
import pygraphviz as pgv
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

databaseInterface.printSQL = False

G=pgv.AGraph(strict=True,directed=True)
linkUUIDtoNodeName = {}

excludedNodes={'61c316a6-0a50-4f65-8767-1f44b1eeb6dd':"default fail procedure for transfers. Too many lines",
               '7d728c39-395f-4892-8193-92f086c0546f':"default fail procedure for SIPs. Too many lines",
               '333532b9-b7c2-4478-9415-28a3056d58df':"reject transfer option.",
               '3467d003-1603-49e3-b085-e58aa693afed':"reject transfer option."}

def addArrow(sourceUUID, destUUID, color="black"):
    if sourceUUID in excludedNodes or destUUID in excludedNodes:
        return
    if sourceUUID == None or destUUID == None:
        return
    G.add_edge(linkUUIDtoNodeName[sourceUUID], linkUUIDtoNodeName[destUUID], color=color)

def loadAllLinks():
    ""
    sql = """SELECT MicroServiceChainLinks.pk, MicroServiceChainLinks.defaultNextChainLink, TasksConfigs.description 
        FROM MicroServiceChainLinks 
        JOIN TasksConfigs ON currentTask = TasksConfigs.pk
        WHERE TasksConfigs.taskType != '5e70152a-9c5b-4c17-b823-c9298c546eeb';"""
    links = databaseInterface.queryAllSQL(sql)
    for link in links:
        pk, defaultNextChainLink, description = link
        if pk in excludedNodes:
            continue
        nodeName = "{%s}%s" % (pk, description)
        G.add_node(nodeName, URL="MicroServiceChainLinks/%s" % pk, label=nodeName, id=nodeName)
        linkUUIDtoNodeName[pk] = nodeName
    for link in links:
        pk, defaultNextChainLink, description = link
        if defaultNextChainLink != None:
            addArrow(pk, defaultNextChainLink)
    return

def bridgeExitCodes():
    ""
    global allLinks
    sql = """SELECT microServiceChainLink, nextMicroServiceChainLink FROM MicroServiceChainLinksExitCodes;"""
    links = databaseInterface.queryAllSQL(sql)
    for link in links:
        microServiceChainLink, nextMicroServiceChainLink = link
        if nextMicroServiceChainLink:
            addArrow(microServiceChainLink, nextMicroServiceChainLink)
    return

def bridgeUserSelections():
    ""
    sql="SELECT MicroServiceChainChoice.choiceAvailableAtLink, MicroServiceChains.startingLink FROM MicroServiceChainChoice JOIN MicroServiceChains ON MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk;"
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        choiceAvailableAtLink, startingLink = row
        if choiceAvailableAtLink and startingLink:
            addArrow(choiceAvailableAtLink, startingLink, color='green')


def bridgeWatchedDirectories():
    ""
    global allLinks
    sql = "SELECT watchedDirectoryPath, startingLink FROM WatchedDirectories Join MicroServiceChains ON WatchedDirectories.chain = MicroServiceChains.pk;"
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        countOfSources = 0
        watchedDirectoryPath, startingLink = row
        sql = "SELECT MicroServiceChainLinks.pk FROM StandardTasksConfigs JOIN TasksConfigs ON TasksConfigs.taskTypePKReference = StandardTasksConfigs.pk JOIN MicroServiceChainLinks ON MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE ( execute LIKE 'moveSIP%%' OR execute LIKE 'moveTransfer%%') AND taskType = '36b2e239-4a57-4aa5-8ebc-7a29139baca6' AND arguments like '%%%s%%';" % (watchedDirectoryPath.replace('%', '\%'))
        rows2 = databaseInterface.queryAllSQL(sql)
        for row2 in rows2:
            microServiceChainLink = row2[0]
            addArrow(microServiceChainLink, startingLink, color="yellow")
            countOfSources +=1
        sql = "SELECT MicroServiceChainLinks.pk FROM StandardTasksConfigs JOIN TasksConfigs ON TasksConfigs.taskTypePKReference = StandardTasksConfigs.pk JOIN MicroServiceChainLinks ON MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE ( execute LIKE 'moveSIP%%' OR execute LIKE 'moveTransfer%%') AND taskType = '36b2e239-4a57-4aa5-8ebc-7a29139baca6' AND arguments like '%%%s%%';" % (watchedDirectoryPath.replace('%watchDirectoryPath%', '%sharedPath%watchedDirectories/', 1).replace('%', '\%'))
        rows2 = databaseInterface.queryAllSQL(sql)
        for row2 in rows2:
            microServiceChainLink = row2[0]
            addArrow(microServiceChainLink, startingLink, color="yellow")
            countOfSources +=1
            
        if countOfSources == 0:
            print "no sources for watched directory: ", watchedDirectoryPath 
            
    return


def bridgeMagicChainLinks():
    ""
    #find the assignments
    sql = "SELECT MicroServiceChainLinks.pk, TasksConfigsAssignMagicLink.execute FROM MicroServiceChainLinks JOIN TasksConfigs ON MicroServiceChainLinks.currentTask = TasksConfigs.pk JOIN TasksConfigsAssignMagicLink ON TasksConfigsAssignMagicLink.pk = TasksConfigs.taskTypePKReference WHERE TasksConfigs.taskType = '3590f73d-5eb0-44a0-91a6-5b2db6655889';"
    rows = databaseInterface.queryAllSQL(sql)
    
    for row in rows:
        microServiceChainLink, magicLink = row
        node = G.get_node(linkUUIDtoNodeName[microServiceChainLink])
    
        visitedNodes = {node:None} #prevents looping    
        count = bridgeMagicChainLinksRecursiveAssist(node, magicLink, visitedNodes)
        if count == 0:
            print "no loads of set link: ", node    
    return

def bridgeMagicChainLinksRecursiveAssist(node, magicLink, visitedNodes):
    ""
    ret = 0
    link = node[1:node.find('}')]
    sql = "SELECT MicroServiceChainLinks.pk FROM MicroServiceChainLinks JOIN TasksConfigs ON MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE TasksConfigs.taskType = '6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9' AND MicroServiceChainLinks.pk = '%s';" % (link)
    #if it's loading it, set the load and return
    rows = databaseInterface.queryAllSQL(sql)
    if len(rows):
        addArrow(link, magicLink, color="brown")
        return 1
    else:
        for neigh in G.neighbors_iter(node):
            if neigh in visitedNodes:
                continue
            visitedNodes[neigh] = None
            ret += bridgeMagicChainLinksRecursiveAssist(neigh, magicLink, visitedNodes)
    return ret
        
    
def bridgeLoadVariable():
    ""
    sql = "SELECT MicroServiceChainLinks.pk, TasksConfigsUnitVariableLinkPull.variable, TasksConfigsUnitVariableLinkPull.defaultMicroServiceChainLink FROM MicroServiceChainLinks JOIN TasksConfigs ON MicroServiceChainLinks.currentTask = TasksConfigs.pk JOIN TasksConfigsUnitVariableLinkPull ON TasksConfigsUnitVariableLinkPull.pk = TasksConfigs.taskTypePKReference WHERE TasksConfigs.taskType = 'c42184a3-1a7f-4c4d-b380-15d8d97fdd11';"
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        count = 0
        microServiceChainLink, variable, defaultMicroServiceChainLink = row
        sql = "SELECT MicroServiceChainLinks.pk, TasksConfigsSetUnitVariable.variable, TasksConfigsSetUnitVariable.microServiceChainLink  FROM MicroServiceChainLinks JOIN TasksConfigs ON MicroServiceChainLinks.currentTask = TasksConfigs.pk JOIN TasksConfigsSetUnitVariable ON TasksConfigsSetUnitVariable.pk = TasksConfigs.taskTypePKReference WHERE TasksConfigs.taskType = '6f0b612c-867f-4dfd-8e43-5b35b7f882d7' AND TasksConfigsSetUnitVariable.variable = '%s';" % (variable)
        rows2 = databaseInterface.queryAllSQL(sql)
        for row2 in rows2:
            microServiceChainLink2, variable,  microServiceChainLinkDest = row2
            addArrow(microServiceChainLink, microServiceChainLinkDest, color="brown")
            count +=1
        if defaultMicroServiceChainLink:
            addArrow(microServiceChainLink, defaultMicroServiceChainLink, color="brown")
        if count == 0:
            print "no bridge variable set for: ", linkUUIDtoNodeName[microServiceChainLink]           
    return

def draw():
    print "Creating"   
    G.layout(prog='dot')
    args= "-Goverlap=prism -v "
    G.draw('test.png', args=args) #firefox
    G.draw('test.svg', args=args) #inkscape
    


def test():
    G.add_node("a")
    G.add_node("b")
    G.add_edge("a", "b")
    draw()
    exit(0)
    
def bridgeSpecial():
    # sip to transfer
    addArrow('39a128e3-c35d-40b7-9363-87f75091e1ff', 'db6d3830-9eb4-4996-8f3a-18f4f998e07f') 
    addArrow('5f99ca60-67b8-4d70-8173-fc22ebda9202', 'db6d3830-9eb4-4996-8f3a-18f4f998e07f')
    
if __name__ == '__main__':
    #test()
    loadAllLinks()
    bridgeExitCodes()
    bridgeUserSelections()
    bridgeWatchedDirectories()
    bridgeLoadVariable()
    bridgeMagicChainLinks()
    bridgeSpecial()
    draw()
    #print G.string()
    #print linkUUIDtoNodeName
    