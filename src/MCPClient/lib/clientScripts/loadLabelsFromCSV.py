#!/usr/bin/env python2

import sys
import csv
import os

import django
django.setup()
# dashboard
from main.models import File

if __name__ == '__main__':
    transferUUID = sys.argv[1]
    fileLabels = sys.argv[2]
    labelFirst = False
    
    if not os.path.isfile(fileLabels):
        print "No such file:", fileLabels
        exit(0)

    # use universal newline mode to support unusual newlines, like \r
    with open(fileLabels, 'rbU') as f:
        reader = csv.reader(f)
        for row in reader:
            if labelFirst:
                label = row[0]
                filePath = row[1]
            else:
                label = row[1]
                filePath = row[0]
            filePath = os.path.join("%transferDirectory%objects/", filePath)
            File.objects.filter(originallocation=filePath, transfer_id=transferUUID).update(label=label)
