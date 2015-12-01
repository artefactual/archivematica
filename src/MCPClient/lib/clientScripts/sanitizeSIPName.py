#!/usr/bin/env python2

from archivematicaMoveSIP import moveSIP
import sys

import django
django.setup()
# dashboard
from main.models import SIP, Transfer

# archivematicaCommon
from custom_handlers import get_script_logger

from sanitizeNames import sanitizePath

DetoxDic={}

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.sanitizeSIPName")

    SIPDirectory = sys.argv[1]
    sipUUID =  sys.argv[2]
    date = sys.argv[3]
    sharedDirectoryPath = sys.argv[4]
    unitType = sys.argv[5]
    #os.path.abspath(SIPDirectory)

    #remove trailing slash
    if SIPDirectory[-1] == "/":
        SIPDirectory = SIPDirectory[:-1]
    
    
    if unitType == "SIP": 
        klass = SIP
        locationColumn = 'currentpath'
    elif unitType == "Transfer":
        klass = Transfer
        locationColumn = 'currentlocation'
    else:
        print >>sys.stderr, "invalid unit type: ", unitType
        exit(1)
    dst = sanitizePath(SIPDirectory)
    if SIPDirectory != dst:
        dst = dst.replace(sharedDirectoryPath, "%sharedPath%", 1) + "/"
        print SIPDirectory.replace(sharedDirectoryPath, "%sharedPath%", 1) + " -> " + dst

        unit = klass.objects.get(uuid=sipUUID)
        setattr(unit, locationColumn, dst)
        unit.save()
