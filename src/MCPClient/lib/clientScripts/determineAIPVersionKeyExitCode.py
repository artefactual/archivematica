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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

import os
import sys
exitCode = 0
from lxml import etree

exitVersionToExitCodeMap = {None: -1, 
                            'Archivematica-0.10': 100}


def getArchivematicaVersionFromMetsXML(mets):
    metsNameSpace = "http://www.loc.gov/METS/"
    for agentIdentifier in mets.iter("{%s}%s" % (metsNameSpace, "agentIdentifier")):
        type = agentIdentifier.find("{%s}%s" % (metsNameSpace, "agentIdentifierType"))
        if type.text != "preservation system":
            continue
        value = agentIdentifier.find("{%s}%s" % (metsNameSpace, "agentIdentifierValue"))
        return value.text


if __name__ == '__main__':
    fauxUUID = sys.argv[1]
    unitPath = sys.argv[2]
    
    basename = os.path.basename(unitPath[:-1])
    uuidLen = 36
    originalSIPName = basename[:-(uuidLen+1)*2]
    originalSIPUUID = basename[:-(uuidLen+1)][-uuidLen:]
    METSPath = os.path.join(unitPath, "data", "METS.%s.xml" % (originalSIPUUID))
    if not os.path.isfile(METSPath):
        print >>sys.stderr, "Mets file not found: ", METSPath
        exit(-1)
        
    parser = etree.XMLParser(remove_blank_text=True)
    metsTree = etree.parse(METSPath, parser)
    mets = metsTree.getroot()
    
    version = getArchivematicaVersionFromMetsXML(mets)
    print version
    
    if version in exitVersionToExitCodeMap:
        exit(exitVersionToExitCodeMap[version])
    exit(exitCode)