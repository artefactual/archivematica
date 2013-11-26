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
import shutil
import traceback
from optparse import OptionParser
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface


def removeDIP(SIPDirectory, SIPUUID):
    try:
        DIP = os.path.join(SIPDirectory, "DIP")
        if os.path.isdir(DIP):
            shutil.rmtree(DIP)
    except Exception as inst:
        traceback.print_exc(file=sys.stdout)
        print type(inst)     # the exception instance
        print inst.args


def removeThumbnails(SIPDirectory, SIPUUID):
    try:
        thumbnails = os.path.join(SIPDirectory, "thumbnails")
        if os.path.isdir(thumbnails):
            shutil.rmtree(thumbnails)
    except Exception as inst:
        traceback.print_exc(file=sys.stdout)
        print type(inst)     # the exception instance
        print inst.args

def removePreservationFiles(SIPDirectory, SIPUUID):
    # Remove Archivematia-created preservation files
    try:
        sql = """SELECT fileUUID, currentLocation FROM Files WHERE SIPUUID = '%s' AND removedTime = 0 AND fileGrpUse = 'preservation';""" % (SIPUUID)
        files = databaseInterface.queryAllSQL(sql)
        for file in files:
            try:
                fileUUID, currentLocation = file
                sql = """UPDATE Files SET removedTime=NOW() WHERE fileUUID = '%s';""" % (fileUUID)
                databaseInterface.runSQL(sql)
                os.remove(currentLocation.replace("%SIPDirectory%", SIPDirectory, 1))
            except Exception as inst:
                traceback.print_exc(file=sys.stdout)
                print type(inst)     # the exception instance
                print inst.args
    except Exception as inst:
        traceback.print_exc(file=sys.stdout)
        print type(inst)     # the exception instance
        print inst.args

    # Remove manually normalized derivation links
    # TODO? Update this to delete for all derivations where the event is deleted
    try:
        sql = """DELETE FROM Derivations USING Derivations JOIN Files ON Derivations.derivedFileUUID = Files.fileUUID WHERE fileGrpUse='manualNormalization' AND sipUUID = '%s';""" % SIPUUID
        databaseInterface.runSQL(sql)
    except Exception as inst:
        traceback.print_exc(file=sys.stdout)
        print type(inst)     # the exception instance
        print inst.args

    # Remove normalization events
    try:
        sql = """DELETE FROM Events USING Events JOIN Files ON Events.fileUUID = Files.fileUUID WHERE eventType='normalization' AND sipUUID = '%s';""" % SIPUUID
        databaseInterface.runSQL(sql)
    except Exception as inst:
        traceback.print_exc(file=sys.stdout)
        print type(inst)     # the exception instance
        print inst.args


if __name__ == '__main__':
    parser = OptionParser()
    #mysql> UPDATE StandardTasksConfigs SET arguments = '--SIPDirectory "%SIPDirectory%" --SIPUUID "%SIPUUID%" --preservation --thumbnails' WHERE PK = '352fc88d-4228-4bc8-9c15-508683dabc58';
    #mysql> UPDATE StandardTasksConfigs SET arguments = '--SIPDirectory "%SIPDirectory%" --SIPUUID "%SIPUUID%" --preservation --thumbnails --access' WHERE PK = 'c15de53e-a5b2-41a1-9eee-1a7b4dd5447a';

    #'--SIPDirectory "%SIPDirectory%" --accessDirectory "objects/access/" --objectsDirectory "objects" --DIPDirectory "DIP" -c'
    parser.add_option("-s",  "--SIPDirectory", action="store", dest="SIPDirectory", default="")
    parser.add_option("-u",  "--SIPUUID", action="store", dest="SIPUUID", default="")
    parser.add_option("-p",  "--preservation", action="store_true", dest="preservation", default=False)
    parser.add_option("-t",  "--thumbnails", action="store_true", dest="thumbnails", default=False)
    parser.add_option("-a",  "--access", action="store_true", dest="access", default=False)  
    (opts, args) = parser.parse_args()

    SIPDirectory = opts.SIPDirectory
    SIPUUID = opts.SIPUUID
    
    if opts.preservation:
        removePreservationFiles(SIPDirectory, SIPUUID)
    if opts.thumbnails:
        removeThumbnails(SIPDirectory, SIPUUID)
    if opts.access:
        removeDIP(SIPDirectory, SIPUUID)
