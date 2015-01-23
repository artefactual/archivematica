#!/usr/bin/python2 -OO

import os
import sys
# archivematicaCommon
from databaseFunctions import fileWasRemoved

REMOVEABLE_FILES = ["Thumbs.db", "Icon", u"Icon\u000D"]

def remove_file(target_file, file_uuid):
    basename = os.path.basename(target_file)
    if basename in REMOVEABLE_FILES:
        print "Removing {filename} (UUID: {uuid})".format(uuid=file_uuid, filename=basename)
        os.remove(target_file)
        # Gearman passes parameters as strings, so None (NoneType) becomes
        # "None" (string)
        if file_uuid and file_uuid != "None":
            fileWasRemoved(file_uuid)

if __name__ == '__main__':
    target = sys.argv[1]
    file_uuid = sys.argv[2]

    sys.exit(remove_file(target, file_uuid))
