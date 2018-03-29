#!/usr/bin/env python2

import logging
import sys

# storageService requires Django to be set up
import django
django.setup()

# archivematicaCommon
import storageService as storage_service

from custom_handlers import get_script_logger

logger = get_script_logger("archivematica.mcp.client.get_aip_storage_locations")

def get_aip_storage_locations(purpose, job):
    """ Return a dict of AIP Storage Locations and their descriptions."""
    storage_directories = storage_service.get_location(purpose=purpose)
    logger.debug("Storage Directories: {}".format(storage_directories))
    choices = {}
    for storage_dir in storage_directories:
        choices[storage_dir['description']] = storage_dir['resource_uri']
    choices['Default location'] = '/api/v2/location/default/{}/'.format(purpose)
    job.pyprint(choices)


def call(jobs):
    for job in jobs:
        with job.JobContext(logger=logger):
            try:
                purpose = job.args[1]
            except IndexError:
                purpose = "AS"

            job.set_status(get_aip_storage_locations(purpose, job))
