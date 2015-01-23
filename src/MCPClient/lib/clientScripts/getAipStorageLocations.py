#!/usr/bin/python2 -OO

import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log",
    level=logging.INFO)

# archivematicaCommon
import storageService as storage_service


def get_aip_storage_locations(purpose):
    """ Return a dict of AIP Storage Locations and their descriptions."""
    storage_directories = storage_service.get_location(purpose=purpose)
    logging.debug("Storage Directories: {}".format(storage_directories))
    choices = {}
    for storage_dir in storage_directories:
        choices[storage_dir['description']] = storage_dir['resource_uri']
    print choices


if __name__ == '__main__':
    try:
        purpose = sys.argv[1]
    except IndexError:
        purpose = "AS"
    get_aip_storage_locations(purpose)
