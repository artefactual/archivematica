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

allLinks = {}

class Links:
    """A simple example class"""
    def __init__(self, pk, linksNext={}):
        global allLinks
        self.pk = pk
        self.linksNext = linksNext
        allLinks[pk] = self
        return
    
    def addLinksNext(self, linksNext):
        "Send a pk string as linksNextArg"
        self.linksNext[linksNext] = None
        return 'hello world'

def loadAllLinks():
    ""
    sql = """SELECT MicroServiceChainLinks.pk, MicroServiceChainLinks.defaultNextChainLink, TasksConfigs.description 
        FROM MicroServiceChainLinks 
        JOIN TasksConfigs ON currentTask = TasksConfigs.pk;"""
    links = databaseInterface.queryAllSQL(sql)
    for link in links:
        pk, defaultNextChainLink, description = link
        linksNext = {}
        if defaultNextChainLink != None:
            linksNext[defaultNextChainLink] = None
        Links(pk, linksNext)
    return

def bridgeExitCodes():
    ""
    global allLinks
    sql = """SELECT microServiceChainLink, nextMicroServiceChainLink FROM MicroServiceChainLinksExitCodes;"""
    links = databaseInterface.queryAllSQL(sql)
    for link in links:
        microServiceChainLink, nextMicroServiceChainLink = link
        if nextMicroServiceChainLink:
            allLinks[microServiceChainLink].addLinksNext(nextMicroServiceChainLink)
    return


def bridgeWatchedDirectories():
    ""
    global allLinks
    sql = "SELECT watchedDirectoryPath, startingLink FROM WatchedDirectories Join MicroServiceChains ON WatchedDirectories.chain = MicroServiceChains.pk;"
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        watchedDirectoryPath, startingLink = row
        sql = "SELECT MicroServiceChainLinks.pk FROM StandardTasksConfigs JOIN TasksConfigs ON TasksConfigs.taskTypePKReference = StandardTasksConfigs.pk JOIN MicroServiceChainLinks ON MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE ( execute LIKE 'moveSIP%%' OR execute LIKE 'moveTransfer%%') AND taskType = '36b2e239-4a57-4aa5-8ebc-7a29139baca6' AND arguments like '%%%s%%';" % (watchedDirectoryPath)
        rows2 = databaseInterface.queryAllSQL(sql)
        for row in rows2:
            microServiceChainLink = row[0]
            allLinks[microServiceChainLink].addLinksNext(startingLink)


    return

def bridgeMagicChainLinks():
    ""
    return
    
def bridgeLoadVariable():
    ""
    return

def draw(allLinks={'1': {'2': None}, '2': {'3': None}, '3': {'2': None}}):
    G=pgv.AGraph(allLinks, strict=True,directed=True)
    small = ['neato','dot','twopi','circo','fdp']
    big = [ 'neato','twopi', 'sfdp']
    for layout in big: #['neato','dot','twopi','circo','fdp']:
        try:
            continue
            print layout
            G.layout(prog=layout)
            #G.layout(prog=layout, args="-Ksfdp")
            #G.draw('%s.png' % (layout), args="-Ksfdp")
            G.draw('%s.png' % (layout))
        except Exception as inst:
            traceback.print_exc(file=sys.stdout)
            print type(inst)     # the exception instance
            print inst.args
    #G.layout(prog='twopi',args='-Gepsilon=10 -mindist=3')
    #G.write("file.dot")
    print "Creating svg"
    
    G.layout(prog='dot')
    G.draw('test.svg', args="-Goverlap=prism -v ")
    

    
    print "Creating png"
    G.layout(prog="dot")
    G.draw('test.png', args="-Goverlap=prism -v ")
    
    print "done printing"
    
    
    
if __name__ == '__main__':
    loadAllLinks()
    bridgeExitCodes()
    bridgeWatchedDirectories()
    bridgeMagicChainLinks()
    bridgeLoadVariable()
    
    #global allLinks
    drawable = {}
    for pk, link in allLinks.iteritems():
        if link.linksNext == {}:
            continue
        drawable[pk] = link.linksNext
    print drawable
    #draw()
    draw(drawable)