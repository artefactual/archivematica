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
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun



def runBag(arguments):
	command = "/usr/share/bagit/bin/bag %s" % (arguments) 
	exitCode, stdOut, stdError = executeOrRun("command", command, printing=False)
	if exitCode != 0:
		print >>sys.stderr, ""
		print >>sys.stderr, "Error with command: ", command
		print >>sys.stderr, "Standard OUT:"
		print >>sys.stderr, stdOut
		print >>sys.stderr, "Standard Error:"
		print >>sys.stderr, stdError
		exit(exitCode)
	else:
		print stdOut
		print >>sys.stderr, stdError

def getListOfDirectories(dir):
	ret = []
	for dir2, subDirs, files in os.walk(dir):
		for subDir in subDirs:
			p = os.path.join(dir2, subDir).replace(dir + "/", "", 1)
			ret.append(p)
		ret.append(dir2.replace(dir + "/", "", 1))
	print "directory list:"
	for dir in ret:
		print "\t", dir
	return ret

def createDirectoriesAsNeeded(baseDir, dirList):
	for dir in dirList:
		directory = os.path.join(baseDir, dir)
		if not os.path.isdir(directory):
			try:
				os.makedirs(directory)
			except:
				continue

if __name__ == '__main__':
	dest = sys.argv[2]
	SIPDir = os.path.dirname(dest)
	dirList = getListOfDirectories(SIPDir)
	arguments = ""
	for s in sys.argv[1:]:
		arguments = "%s \"%s\"" % (arguments, s)
	runBag(arguments)
	createDirectoriesAsNeeded(os.path.join(dest, "data"), dirList)
