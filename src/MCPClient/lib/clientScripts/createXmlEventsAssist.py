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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import lxml.etree as etree
import ConfigParser

config2 = ConfigParser.SafeConfigParser()
config2.read("/etc/archivematica/MCPClient/clientConfig.conf")

config = ConfigParser.SafeConfigParser()
config.read(config2.get('MCPClient', "sharedDirectoryMounted") + "sharedMicroServiceTasksConfigs/createXmlEventsAssist/organization.ini")


yourAgentIdentifierType=config.get('organization', "yourAgentIdentifierType")
yourAgentIdentifierValue=config.get('organization', "yourAgentIdentifierValue")
yourAgentName=config.get('organization', "yourAgentName")
yourAgentType=config.get('organization', "yourAgentType")

organizationEvents = ["receive SIP", "SIP review", "appraise SIP"]

def createLinkingAgentIdentifierAssist(linkingAgentIdentifierType, linkingAgentIdentifierValue):
    ret = etree.Element("linkingAgentIdentifier")
    etree.SubElement(ret, "linkingAgentIdentifierType").text = linkingAgentIdentifierType
    etree.SubElement(ret, "linkingAgentIdentifierValue").text = linkingAgentIdentifierValue
    return ret

def createArchivematicaLinkingAgentIdentifier():
    return createLinkingAgentIdentifierAssist("preservation system", "Archivematica-0.7")

def createOrgLinkingAgentIdentifier():
    return createLinkingAgentIdentifierAssist(yourAgentIdentifierType, yourAgentIdentifierValue)

def createAgent(agentIdentifierType, agentIdentifierValue, agentName, agentType):
    ret = etree.Element("agent")
    agentIdentifier = etree.SubElement( ret, "agentIdentifier")
    etree.SubElement( agentIdentifier, "agentIdentifierType").text = agentIdentifierType
    etree.SubElement( agentIdentifier, "agentIdentifierValue").text = agentIdentifierValue
    etree.SubElement( ret, "agentName").text = agentName
    etree.SubElement( ret, "agentType").text = agentType
    return ret


def createArchivematicaAgent():
    return createAgent("preservation system", "Archivematica-0.7", "Archivematica", "software")

def createOrganizationAgent():
    return createAgent(yourAgentIdentifierType, yourAgentIdentifierValue, yourAgentName, yourAgentType)

def createLinkingAgentIdentifier(eType):
    if eType in organizationEvents:
        return createOrgLinkingAgentIdentifier()
    else:
        return createArchivematicaLinkingAgentIdentifier()


def createOutcomeInformation( eventOutcomeDetailNote = None, eventOutcomeText = None):
    ret = etree.Element("eventOutcomeInformation")
    etree.SubElement(ret, "eventOutcome").text = eventOutcomeText
    eventOutcomeDetail = etree.SubElement(ret, "eventOutcomeDetail")
    etree.SubElement(eventOutcomeDetail, "eventOutcomeDetailNote").text = eventOutcomeDetailNote
    return ret

def createEvent( eIDValue, eType, eIDType="UUID", \
eventDateTime = "now", \
eventDetailText = "", \
eOutcomeInformation = createOutcomeInformation(), \
linkingAgentIdentifier = None):
    ret = etree.Element("event")
    eventIdentifier = etree.SubElement(ret, "eventIdentifier")
    etree.SubElement(eventIdentifier, "eventIdentifierType").text = eIDType
    etree.SubElement(eventIdentifier, "eventIdentifierValue").text = eIDValue
    etree.SubElement(ret, "eventType").text = eType
    etree.SubElement(ret, "eventDateTime").text = eventDateTime
    eDetail = etree.SubElement(ret, "eventDetail")
    eDetail.text = eventDetailText
    if eOutcomeInformation != None:
        ret.append(eOutcomeInformation)
    if not linkingAgentIdentifier:
        linkingAgentIdentifier = createLinkingAgentIdentifier(eType)
    ret.append(linkingAgentIdentifier)
    return ret

if __name__ == '__main__':
    print "This is a support file."
    print "testing..."
    event = createEvent("test", "test")
    print etree.tostring(event, pretty_print=True)
