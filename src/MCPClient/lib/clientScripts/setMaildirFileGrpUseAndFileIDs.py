#!/usr/bin/env python2

import os
import sys
exitCode = 0

# archivematicaCommon
from custom_handlers import get_script_logger
from externals.extractMaildirAttachments import parse
import databaseInterface


def setArchivematicaMaildirFiles(sipUUID, sipPath):
    for root, dirs, files in os.walk(os.path.join(sipPath, "objects", "attachments")):
        for file in files:
            if file.endswith('.archivematicaMaildir'):
                fileRelativePath = os.path.join(root, file).replace(sipPath, "%SIPDirectory%", 1)
                sql = """SELECT fileUUID FROM Files WHERE removedTime = 0 AND sipUUID = %s AND currentLocation = %s;"""
                rows = databaseInterface.queryAllSQL(sql, (sipUUID, fileRelativePath))
                if len(rows):
                    fileUUID = rows[0][0]
                    sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES (%s, (SELECT pk FROM FileIDs WHERE enabled = TRUE AND description = 'A .archivematicaMaildir file')); """
                    databaseInterface.runSQL(sql, (fileUUID,))
        
def setMaildirFiles(sipUUID, sipPath):
    for root, dirs, files in os.walk(os.path.join(sipPath, "objects", "Maildir")):
        for file in files:
            fileRelativePath = os.path.join(root, file).replace(sipPath, "%SIPDirectory%", 1)
            sql = """SELECT fileUUID FROM Files WHERE removedTime = 0 AND sipUUID = %s AND currentLocation = %s;"""
            rows = databaseInterface.queryAllSQL(sql, (sipUUID, fileRelativePath))
            if len(rows):
                fileUUID = rows[0][0]
                sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES (%s, (SELECT pk FROM FileIDs WHERE enabled = TRUE AND description = 'A maildir email file')); """
                databaseInterface.runSQL(sql, (fileUUID,))
    
    

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.setMaildirFileGrpUseAndFileIDs")

    sipUUID = sys.argv[1]
    sipPath = sys.argv[2]
    setMaildirFiles(sipUUID, sipPath)    
    setArchivematicaMaildirFiles(sipUUID, sipPath)
    
    exit(exitCode)
