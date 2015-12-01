#!/usr/bin/env python2

import os
import sys
target = sys.argv[1]
if not os.path.isdir(target):
    print >>sys.stderr, "Directory doesn't exist: ", target
    os.mkdir(target)
if os.listdir(target) == []:
    print >>sys.stderr, "Directory is empty: ", target
    fileName = os.path.join(target, "submissionDocumentation.log")
    f = open(fileName, 'a')
    f.write("No submission documentation added")
    f.close()
    os.chmod(fileName, 488)
else:
    exit(0)
