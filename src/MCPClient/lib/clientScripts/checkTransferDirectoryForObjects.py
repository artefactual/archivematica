#!/usr/bin/env python2

import os
import sys
exitInidcatingThereAreObjects = 179

if __name__ == '__main__':
    objectsDir = sys.argv[1]
    os.path.isdir(objectsDir)
    ret = 0
    for dirs, subDirs, files in os.walk(objectsDir):
        if files != None and files != []:
            ret = exitInidcatingThereAreObjects
            break
    exit(ret)
