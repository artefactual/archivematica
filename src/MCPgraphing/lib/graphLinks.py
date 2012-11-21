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

G=pgv.AGraph(strict=True,directed=True)
linkUUIDtoNodeName = {}

excludedNodes={'61c316a6-0a50-4f65-8767-1f44b1eeb6dd':"default fail procedure for transfers. Too many lines",
               '7d728c39-395f-4892-8193-92f086c0546f':"default fail procedure for SIPs. Too many lines",
               '333532b9-b7c2-4478-9415-28a3056d58df':"reject transfer option."}

def addArrow(sourceUUID, destUUID, color="black"):
    if sourceUUID in excludedNodes or destUUID in excludedNodes:
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
        G.add_node(nodeName)
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
        watchedDirectoryPath, startingLink = row
        sql = "SELECT MicroServiceChainLinks.pk FROM StandardTasksConfigs JOIN TasksConfigs ON TasksConfigs.taskTypePKReference = StandardTasksConfigs.pk JOIN MicroServiceChainLinks ON MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE ( execute LIKE 'moveSIP%%' OR execute LIKE 'moveTransfer%%') AND taskType = '36b2e239-4a57-4aa5-8ebc-7a29139baca6' AND arguments like '%%%s%%';" % (watchedDirectoryPath)
        rows2 = databaseInterface.queryAllSQL(sql)
        for row2 in rows2:
            microServiceChainLink = row2[0]
            addArrow(microServiceChainLink, startingLink, color="yellow")
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
        bridgeMagicChainLinksRecursiveAssist(node, magicLink, visitedNodes)
    
    return

def bridgeMagicChainLinksRecursiveAssist(node, magicLink, visitedNodes):
    ""
    link = node[1:node.find('}')]
    sql = "SELECT MicroServiceChainLinks.pk FROM MicroServiceChainLinks JOIN TasksConfigs ON MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE TasksConfigs.taskType = '6fe259c2-459d-4d4b-81a4-1b9daf7ee2e9' AND MicroServiceChainLinks.pk = '%s';" % (link)
    #if it's loading it, set the load and return
    rows = databaseInterface.queryAllSQL(sql)
    if len(rows):
        addArrow(link, magicLink, color="brown")
        return
    else:
        for neigh in G.neighbors_iter(node):
            if neigh in visitedNodes:
                continue
            visitedNodes[neigh] = None
            bridgeMagicChainLinksRecursiveAssist(neigh, magicLink, visitedNodes)
    
def bridgeLoadVariable():
    ""
    return

def draw():
    print "Creating svg"   
    G.layout(prog='dot')
    G.draw('test.svg', args="-Goverlap=prism -v ")
    


def test():
    G.add_node("a")
    G.add_node("b")
    G.add_edge("a", "b")
    draw()
    exit(0)
    
if __name__ == '__main__':
    #test()
    loadAllLinks()
    bridgeExitCodes()
    bridgeUserSelections()
    bridgeWatchedDirectories()
    bridgeMagicChainLinks()
    bridgeLoadVariable()
    draw()
    #print G.string()
    #print linkUUIDtoNodeName
    