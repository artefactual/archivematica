#!/usr/bin/env python2

import json

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
    logger.debug(
        "Storage Directories: {}".format(
            json.dumps(storage_directories, indent=4, sort_keys=True)
        )
    )
    choices = {}
    for storage_dir in storage_directories:
        label = storage_dir["description"]
        if not label:
            label = storage_dir["relative_path"]
        choices[storage_dir["uuid"]] = {
            "description": label,
            "uri": storage_dir["resource_uri"],
        }
    choices["default"] = {
        "description": "Default Location",
        "uri": "/api/v2/location/default/{}/".format(purpose),
    }
    job.pyprint(json.dumps(choices, indent=4, sort_keys=True))


def call(jobs):
    for job in jobs:
        with job.JobContext(logger=logger):
            try:
                purpose = job.args[1]
            except IndexError:
                purpose = "AS"

            job.set_status(get_aip_storage_locations(purpose, job))
