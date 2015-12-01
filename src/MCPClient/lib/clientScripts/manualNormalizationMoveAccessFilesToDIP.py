#!/usr/bin/env python2

import os
import sys

import django
django.setup()
from django.db.models import Q
# dashboard
from main.models import File

# archivematicaCommon
import fileOperations

#--sipUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%"
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-s",  "--sipUUID", action="store", dest="sipUUID", default="")
parser.add_option("-d",  "--sipDirectory", action="store", dest="sipDirectory", default="") #transferDirectory/
parser.add_option("-f",  "--filePath", action="store", dest="filePath", default="") #transferUUID/sipUUID
(opts, args) = parser.parse_args()

# Search for original file associated with the access file given in filePath
filePathLike = opts.filePath.replace(os.path.join(opts.sipDirectory, "objects", "manualNormalization", "access"), "%SIPDirectory%objects", 1)
i = filePathLike.rfind(".")
if i != -1:
    # Matches "path/to/file/filename." Includes . so it doesn't false match foobar.txt when we wanted foo.txt
    filePathLike = filePathLike[:i+1]
    # Matches the exact filename.  For files with no extension.
    filePathLike2 = filePathLike[:-1]
     
unitIdentifierType = "sip_id"
unitIdentifier = opts.sipUUID

try:
    kwargs = {
        "removedtime__isnull": True,
        "filegrpuse": "original",
        unitIdentifierType: unitIdentifier
    }
    try:
        f = File.objects.get(currentlocation__startswith=filePathLike,
                             **kwargs)
    except (File.DoesNotExist, File.MultipleObjectsReturned):
        f = File.objects.get(currentlocation=filePathLike2,
                             **kwargs)
except (File.DoesNotExist, File.MultipleObjectsReturned) as e:
    # Original file was not found, or there is more than one original file with
    # the same filename (differing extensions)
    # Look for a CSV that will specify the mapping
    csv_path = os.path.join(opts.sipDirectory, "objects", "manualNormalization", 
        "normalization.csv")
    if os.path.isfile(csv_path):
        try:
            access_file = opts.filePath[opts.filePath.index('manualNormalization/access/'):]
        except ValueError:
            print >>sys.stderr, "{0} not in manualNormalization directory".format(opts.filePath)
            exit(4)
        original = fileOperations.findFileInNormalizatonCSV(csv_path,
            "access", access_file, unitIdentifier)
        if original is None:
            if isinstance(e, File.DoesNotExist):
                print >>sys.stderr, "No matching file for: {0}".format(
                    opts.filePath.replace(opts.sipDirectory, "%SIPDirectory%"))
                exit(3)
            else:
                print >>sys.stderr, "Could not find {access_file} in {filename}".format(
                        access_file=access_file, filename=csv_path)
                exit(2)
        # If we found the original file, retrieve it from the DB
        kwargs = {
            "removedtime__isnull": True,
            "filegrpuse": "original",
            "originallocation__endswith": original,
            unitIdentifierType: unitIdentifier
        }
        f = File.objects.get(**kwargs)
    else:
        if isinstance(e, File.DoesNotExist):
            print >>sys.stderr, "No matching file for: ", opts.filePath.replace(opts.SIPDirectory, "%SIPDirectory%", 1)
            exit(3)
        elif isinstance(e, File.MultipleObjectsReturned):
            print >>sys.stderr, "Too many possible files for: ", opts.filePath.replace(opts.SIPDirectory, "%SIPDirectory%", 1)
            exit(2)

# We found the original file somewhere above, get the UUID and path
originalFileUUID = f.uuid
originalFilePath = f.originallocation

print "matched: {%s}%s" % (originalFileUUID, originalFilePath)
dstDir = os.path.join(opts.sipDirectory, "DIP", "objects")
dstFile = originalFileUUID + "-" + os.path.basename(opts.filePath)

#ensure unique output file name
i = 0
while os.path.exists(os.path.join(dstDir, dstFile)):
    i+=1
    dstFile = originalFileUUID + "-" + str(i) + "-" + os.path.basename(opts.filePath)
    
try:
    if not os.path.isdir(dstDir):
        os.makedirs(dstDir)
except:
    pass

#Rename the file or directory src to dst. If dst is a directory, OSError will be raised. On Unix, if dst exists and is a file, it will be replaced silently if the user has permission. The operation may fail on some Unix flavors if src and dst are on different filesystems.
#see http://docs.python.org/2/library/os.html
os.rename(opts.filePath, os.path.join(dstDir, dstFile))

exit(0)
