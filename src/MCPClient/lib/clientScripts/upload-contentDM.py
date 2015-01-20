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
# @author Mark Jordan <mark2jordan@gmail.com>

import os
import sys
import glob
import argparse
import json
import urllib
from urlparse import urlparse
import re

# This function queries the CONTENTdm collection configuration to determine
# where the collection's import directory is on the server.
def getDestinationImportDirectory(targetCollection, contentdmServer):
  try:
    CollectionParametersUrl = contentdmServer + '?q=dmGetCollectionParameters' + targetCollection + '/json'
    f = urllib.urlopen(CollectionParametersUrl)
    collectionParametersString = f.read()
    collectionParameters = json.loads(collectionParametersString)
  except:
    print >>sys.stderr, "Cannot retrieve CONTENTdm collection parameters from " + CollectionParametersUrl
    quit(1)

  return collectionParameters['path']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='restructure')
    parser.add_argument('--uuid', action="store", dest='uuid', metavar='UUID', help='AIP-UUID')
    parser.add_argument('--server', action="store", dest='contentdmServer', metavar='server',
        help='Target CONTENTdm server')
    parser.add_argument('--username', action="store", dest='contentdmUser', metavar='server',
         help='Username for rsyncing the DIP to the CONTENTdm server')
    parser.add_argument('--group', action="store", dest='contentdmGroup', metavar='server',
         help='Group (numeric) ID for rsyncing the DIP to the CONTENTdm server')
    parser.add_argument('--collection', action="store", dest='targetCollection',
         metavar='targetCollection', help='Target CONTENTdm Collection')
    parser.add_argument('--outputDir', action="store", dest='outputDir', metavar='outputDir',
         help='The location of the restructured DIPs')

    args = parser.parse_args()
    
    # Before proceeding, check to see if there is a zip file for this DIP; if there is,
    # the user has selected the 'Project Client' option and we just exit from this script.
    projectClientZipPath = outputDipDir = os.path.join(args.outputDir, 'CONTENTdm', 'projectclient', args.uuid + '.7z')
    if os.path.exists(projectClientZipPath):
        quit(0)

    # If we haven't quit, continue to process the 'directupload' files.
    contentdmCollectionDirectory = getDestinationImportDirectory(args.targetCollection, args.contentdmServer)

    # Determine if the package is for a simple item or a compound item by counting the
    # number of .desc files in the DIP directory. If it's simple, append 'import' to the
    # end of destinationImportDirectory; if it's compound, append 'import/cdoc' to the end.
    sourceDescFiles =  glob.glob(os.path.join(args.outputDir, 'CONTENTdm', 'directupload', args.uuid, "*.desc"))
    if len(sourceDescFiles) > 0:
        packageType = 'simple'
        destinationImportDirectory = os.path.join(contentdmCollectionDirectory, 'import')
    else:
        packageType = 'compound'
        destinationImportDirectory = os.path.join(contentdmCollectionDirectory, 'import', 'cdoc')

    # We need to remove the port, if any, from server, since we don't use it while scping or sshing.
    contentdmServerParts = urlparse(args.contentdmServer)
    match = re.search(r':.+$', contentdmServerParts.netloc)
    if match:
        contentdmServerHostname = re.sub(r':.+$', '', contentdmServerParts.netloc)
    else:
        contentdmServerHostname = contentdmServerParts.netloc
    
    rsyncDestPath = args.contentdmUser + '@' + contentdmServerHostname + ':' + destinationImportDirectory

    sourceDir = os.path.join(args.outputDir, 'CONTENTdm', 'directupload', args.uuid)
    sourceFiles = os.listdir(sourceDir)
        
    rsyncCmd = "rsync -rv %s %s " % (sourceDir + '/', rsyncDestPath)
    print "rsyc command: ", rsyncCmd
    rsyncExitCode = os.system(rsyncCmd)
    if rsyncExitCode != 0:
        print "Error copying direct upload files to " + rsyncDestPath
        print "Error code: ", rsyncExitCode
        quit(1)
    print "rsyncCmd: " + rsyncCmd

    # Loop through all the files or directories and change their group and permisions.
    for sourceFilename in sourceFiles:
        # Change the permissions and group of the DIP files so they are correct on the CONTENTdm
        sshLogin = args.contentdmUser + "@" + contentdmServerHostname
        sshChgrpCmd = 'chgrp -R ' + args.contentdmGroup 
        sshChmodCmd = 'chmod -R g+rw'
        destPath = os.path.join(destinationImportDirectory, sourceFilename)
        sshCmd = 'ssh %s "%s %s && %s %s"' % (sshLogin, sshChgrpCmd, destPath, sshChmodCmd, destPath)
        sshExitCode = os.system(sshCmd)
        if sshExitCode != 0:
            print "Error setting attributes of file " + destPath
            print "Error code: ", sshExitCode
            quit(1)
        print "sshCmd : " + sshCmd

