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
# @subpackage Ingest
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import sys

def validLine(line):
    if not line:
        return False
    elif line.isspace():
        return False
    elif len(line.split("=",1)) != 2:
        return False
    else:
        return True

def checkForVars(varsDic, var, varValue):

    splits = varValue.split("${",1)
    while len(splits) == 2:
        splits2 = splits[1].split("}",1)
        if len(splits2) == 2:
            variable = splits2[0]
            varValue = varValue.replace("${" + variable + "}", varsDic[variable])
        else:
            print "error with line: " + var + " = " + VarValue
            return varValue
        splits = varValue.split("${",1)
    return varValue


def loadConfig(configFile="/etc/archivematica/archivematicaConfig.conf"):
    configFile_fh = open(configFile, "r")
    line = configFile_fh.readline()
    varsDic={}
    while line:
        #remove comments
        line = line.split("#",1)[0]
        if validLine(line):
            varline = line.split("=",1)
            var = varline[0]
            varValue = varline[1]
            varValue = varValue.replace( "\n", "", 1)
            varValue = checkForVars(varsDic, var, varValue)
            varValue = varValue.split("\"")[1]
            varsDic[var] = varValue
        line = configFile_fh.readline()

    # TODO
    # recursively look for variables and replace them in the values - would be best in new function

    return varsDic


if __name__ == '__main__':
    ret = loadConfig(sys.argv[1])
    print ret
