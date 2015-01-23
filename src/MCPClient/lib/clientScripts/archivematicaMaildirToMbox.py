#!/usr/bin/python -OO
import sys
import os
# archivematicaCommon
from externals.maildirToMbox import maildir2mailbox2


def getFileDic(fileFullPath):
    f = open(fileFullPath, 'r')
    #for line in f.readlines():
    fileDic = {}
    for line in f:
        if line.startswith('#'):
            continue
        else:
            eqIndex = line.find('=')
            if eqIndex != -1:
                key = line[:eqIndex].strip()
                value =  line[eqIndex+1:].strip()
                fileDic[key] = value
    f.close()
    return fileDic

if __name__ == "__main__":
    while 0:
        import time
        time.sleep(10)
    fileFullPath = sys.argv[1]
    mboxOutputFileFullPath = sys.argv[2]
    
    sipDirectory = os.path.dirname(os.path.dirname(os.path.dirname(fileFullPath)))
    fileDic = getFileDic(fileFullPath)
    if not 'path' in fileDic:
        print >>sys.stderr, "no path in file"
        exit(1)
    maildirPath = fileDic['path'].replace('%transferDirectory%', sipDirectory + "/", 1)
    print maildirPath, " -> ", mboxOutputFileFullPath
    maildir2mailbox2(maildirPath, mboxOutputFileFullPath)
    print "Done" 
    exit(0)
    
    
    