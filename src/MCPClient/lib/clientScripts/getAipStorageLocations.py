#!/usr/bin/env python2

import logging
import sys

# storageService requires Django to be set up
import django
django.setup()

# archivematicaCommon
from custom_handlers import get_script_logger
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
    logger = get_script_logger("archivematica.mcp.client.getAipStorageLocations")

    try:
        purpose = sys.argv[1]
    except IndexError:
        purpose = "AS"
    get_aip_storage_locations(purpose)
