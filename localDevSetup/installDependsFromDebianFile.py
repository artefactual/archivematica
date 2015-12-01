#!/usr/bin/env python2

#Depends: ${shlibs:Depends}, ${misc:Depends}, libapache2-mod-wsgi, python-django, python-django-doc
import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
excludePackages = ["sip-creation-tools", "sanitize-names"]


filePath = sys.argv[1]
if not os.path.isfile(filePath):
    print >>sys.stderr, "File doesn't exist."
    exit(2)
f = open(filePath, 'r')

line = f.readline()
while not line.startswith("Depends:"):
    line = f.readline()

# Depends: statements can span lines
followup = f.readline()
while followup.startswith((' ', '\t')):
    line = line + followup
    followup = f.readline()

for part in line.split(","):
    # The word is split in order to try to install the latest version of
    # packages expressed in the syntax: foo (>= bar)
    # TODO apt-get install doesn't appear to support the full version
    # syntax control files support, but this should possibly try to
    # install the exact version specified?
    part = part.strip().split(' ')[0]
    if part.find("${shlibs:Depends}") != -1 or \
        part.find("${misc:Depends}") != -1:
        continue
    if part.startswith(("archivematica", "Depends:")):
        continue

    if part in excludePackages:
        continue

    print sys.argv[1]
    print "Attempting Install/Update of: ", part
    command = "sudo apt-get install -y " + part
    exitCode, stdOut, stdError = executeOrRun("command", command, printing=False)
    if exitCode:
        print "exitCode:", exitCode
        print stdOut
        print >>sys.stderr, stdError
    #else:
        #print "OK"
