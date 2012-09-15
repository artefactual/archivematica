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
# @subpackage archivematicaClient
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

class accessTranscoderObject:
    def __init__(self, commandID):
        fileTitle = ""
    fileExtension = ""
    fileDirectory = ""
    fileFullName = ""
    
    def getReplacementDic(self):
        return {}


def setFileIn(fileIn=sys.argv[1]):
    global fileTitle
    global fileExtension
    global fileDirectory
    global fileFullName
    #get file name and extension
    s = fileIn
    #get indexes for python string array
    #index of next char after last /
    x1 = s.rfind('/')+1
    #index of last .
    x2 = s.rfind('.')
    #index of next char after last .
    x2mod = x2+1
    #length of s
    sLen = len(s)

    if x2 < x1:
        x2mod = 0


    fileDirectory = os.path.dirname(s) + "/"
    if x2mod != 0:
        fileExtension = s[x2mod:sLen]
        fileTitle = s[x1:x2]
        fileFullName = fileDirectory + fileTitle + "." + fileExtension
    else:
        #print "No file extension!"
        fileExtension = ""
        fileTitle = s[x1:sLen]
        fileFullName = fileDirectory + fileTitle
