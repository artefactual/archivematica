#!/usr/bin/env python2

import os
import sys
from lxml import etree

import archivematicaXMLNamesSpace

import django
django.setup()
# dashboard
from main.models import File

def identify_dspace_files(mets_file, transfer_dir, transfer_uuid, relative_dir="./"):
    print mets_file
    nsmap = {
        'm': archivematicaXMLNamesSpace.metsNS,
        'x': archivematicaXMLNamesSpace.xlinkNS,
    }
    tree = etree.parse(mets_file)
    root = tree.getroot()
    for item in root.findall("m:fileSec/m:fileGrp", namespaces=nsmap):
        use = item.get("USE")
        if use in ('TEXT', 'LICENSE'):
            try:
                filename = item.find('m:file/m:FLocat', namespaces=nsmap).get(archivematicaXMLNamesSpace.xlinkBNS+'href')
            except AttributeError:  # Element not found
                continue
            if filename is None: # Filename not an attribute
                continue
            print 'File:', filename, 'Use:', use
            full_path = os.path.join(relative_dir, filename)
            db_location = full_path.replace(transfer_dir, "%transferDirectory%")
            if use == 'TEXT':
                db_use = 'text/ocr'
            elif use == 'LICENSE':
                db_use = 'license'
            else:
                print >> sys.stderr, 'Unexpected usage', use
                continue

            File.objects.filter(currentlocation=db_location, transfer_id=transfer_uuid).update(filegrpuse=db_use)


if __name__ == '__main__':
    mets_file = sys.argv[1]
    transfer_dir = sys.argv[2]
    transfer_uuid = sys.argv[3]

    identify_dspace_files(mets_file, transfer_dir, transfer_uuid, relative_dir=os.path.dirname(mets_file) + "/")
