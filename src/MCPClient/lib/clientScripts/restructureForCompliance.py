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

import os
import sys
import shutil
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from fileOperations import updateDirectoryLocation
from fileOperations import updateFileLocation2


requiredDirectories = ["logs", "logs/fileMeta", "metadata", "metadata/submissionDocumentation", "objects"]
optionalFiles = "processingMCP.xml"

def restructureBagForComplianceFileUUIDsAssigned(unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith = "%transferDirectory%"):
	bagFileDefaultDest = os.path.join(unitPath, "logs", "BagIt")
	requiredDirectories.append(bagFileDefaultDest)
	unitDataPath = os.path.join(unitPath, "data")
	for dir in requiredDirectories:
		dirPath = os.path.join(unitPath, dir)
		dirDataPath = os.path.join(unitPath, "data", dir)
		if os.path.isdir(dirDataPath):
			#move to the top level
			src = dirDataPath 
			dst = dirPath
			updateDirectoryLocation(src, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
			print "moving directory ", dir 
		else:
			print "creating: ", dir
			os.mkdir(dirPath)
	for item in os.listdir(unitPath):
		src = os.path.join(unitPath, item)
		if os.path.isfile(src):
			if item.startswith("manifest"):
				dst = os.path.join(unitPath, "metadata", item)
			else:
				dst = os.path.join(bagFileDefaultDest, item)
			updateFileLocation2(src, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
	for item in os.listdir(unitDataPath):
		itemPath =  os.path.join(unitDataPath, item)
		if os.path.isdir(itemPath) and item not in requiredDirectories:
			print "moving directory to objects: ", item
			dst = os.path.join(unitPath, "objects", item)
			updateDirectoryLocation(itemPath, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
		elif os.path.isfile(itemPath) and item not in optionalFiles:
			print "moving file to objects: ", item
			dst = os.path.join(unitPath, "objects", item)
			updateFileLocation2(itemPath, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
	print "removing empty data directory"
	os.rmdir(unitDataPath)

def restructureForComplianceFileUUIDsAssigned(unitPath, unitIdentifier, unitIdentifierType):
	print "Not implemented"
	print unitUUID, unitType

def restructureDirectory(unitPath):
	for dir in requiredDirectories:
		dirPath = os.path.join(unitPath, dir)
		if not os.path.isdir(dirPath):
			os.mkdir(dirPath)
			print "creating: ", dir
	for item in os.listdir(unitPath):
		dst = os.path.join(unitPath, "objects") + "/."
		itemPath =  os.path.join(unitPath, item)
		if os.path.isdir(itemPath) and item not in requiredDirectories:
			shutil.move(itemPath, dst)
			print "moving directory to objects: ", item
		elif os.path.isfile(itemPath) and item not in optionalFiles:
			shutil.move(itemPath, dst)
			print "moving file to objects: ", item

if __name__ == '__main__':
	target = sys.argv[1]
	restructureDirectory(target)
	
