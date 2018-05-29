#!/usr/bin/env python2

from __future__ import print_function
import argparse
import sys

import requests

import django
django.setup()
from django.conf import settings as mcpclient_settings
# dashboard
from main import models

# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions
from lib.job_email_report import run_report
import storageService as storage_service

logger = get_script_logger("archivematica.mcp.client.post_store_aip_hook")

COMPLETED = 0
NO_ACTION = 1
ERROR = 2


def dspace_handle_to_archivesspace(sip_uuid):
    """Fetch the DSpace handle from the Storage Service and send to ArchivesSpace."""
    # Get association to ArchivesSpace if it exists
    try:
        digital_object = models.ArchivesSpaceDigitalObject.objects.get(sip_id=sip_uuid)
    except models.ArchivesSpaceDigitalObject.DoesNotExist:
        print('SIP', sip_uuid, 'not associated with an ArchivesSpace component')
        return NO_ACTION
    print('Digital Object', digital_object.remoteid, 'for SIP', digital_object.sip_id, 'found')
    logger.info('Digital Object %s for SIP %s found', digital_object.remoteid, digital_object.sip_id)

    # Get dspace handle from SS
    file_info = storage_service.get_file_info(uuid=sip_uuid)[0]
    try:
        handle = file_info['misc_attributes']['handle']
    except KeyError:
        print('AIP has no DSpace handle stored')
        return NO_ACTION
    print('DSpace handle:', handle)
    logger.info('DSpace handle: %s', handle)

    # POST Dspace handle to ArchivesSpace
    # Get ArchivesSpace config
    config = models.DashboardSetting.objects.get_dict('upload-archivesspace_v0.0')
    archivesspace_url = 'http://' + config['host'] + ':' + str(config['port'])

    # Log in
    url = archivesspace_url + '/users/' + config['user'] + '/login'
    params = {'password': config['passwd']}
    logger.debug('Log in to ArchivesSpace URL: %s', url)
    response = requests.post(url, params=params, timeout=mcpclient_settings.AGENTARCHIVES_CLIENT_TIMEOUT)
    logger.debug('Response: %s %s', response, response.content)
    session_id = response.json()['session']
    headers = {'X-ArchivesSpace-Session': session_id}

    # Get Digital Object from ArchivesSpace
    url = archivesspace_url + digital_object.remoteid
    logger.debug('Get Digital Object info URL: %s', url)
    response = requests.get(url, headers=headers, timeout=mcpclient_settings.AGENTARCHIVES_CLIENT_TIMEOUT)
    logger.debug('Response: %s %s', response, response.content)
    body = response.json()

    # Update
    url = archivesspace_url + digital_object.remoteid
    file_version = {
        "file_uri": handle,
        "use_statement": config['use_statement'],
        "xlink_show_attribute": config['xlink_show'],
        "xlink_actuate_attribute": config['xlink_actuate'],
    }
    body['file_versions'].append(file_version)
    logger.debug('Modified Digital Object: %s', body)
    response = requests.post(url, headers=headers, json=body, timeout=mcpclient_settings.AGENTARCHIVES_CLIENT_TIMEOUT)
    print('Update response:', response, response.content)
    logger.debug('Response: %s %s', response, response.content)
    if response.status_code != 200:
        print('Error updating', digital_object.remoteid)
        return ERROR
    return COMPLETED


def post_store_hook(sip_uuid):
    """
    Hook for doing any work after an AIP is stored successfully.
    """
    if not mcpclient_settings.SEARCH_ENABLED:
        logger.info('Skipping indexing: indexing is currently disabled.')
        return 0

    elasticSearchFunctions.setup_reading_from_conf(mcpclient_settings)
    client = elasticSearchFunctions.get_client()

    # SIP ARRANGEMENT

    # Mark files in this SIP as in an AIP (aip_created)
    file_uuids = models.File.objects.filter(sip=sip_uuid).values_list('uuid', flat=True)
    models.SIPArrange.objects.filter(file_uuid__in=file_uuids).update(aip_created=True)

    # Check if any of component transfers are completely stored
    # TODO Storage service should index AIPs, knows when to update ES
    transfer_uuids = set(models.SIPArrange.objects.filter(file_uuid__in=file_uuids).values_list('transfer_uuid', flat=True))
    for transfer_uuid in transfer_uuids:
        print('Checking if transfer', transfer_uuid, 'is fully stored...')
        arranged_uuids = set(models.SIPArrange.objects.filter(transfer_uuid=transfer_uuid).filter(aip_created=True).values_list('file_uuid', flat=True))
        backlog_uuids = set(models.File.objects.filter(transfer=transfer_uuid).values_list('uuid', flat=True))
        # If all backlog UUIDs have been arranged
        if arranged_uuids == backlog_uuids:
            print('Transfer', transfer_uuid, 'fully stored, sending delete request to storage service, deleting from transfer backlog')
            # Submit delete req to SS (not actually delete), remove from ES
            storage_service.request_file_deletion(
                uuid=transfer_uuid,
                user_id=0,
                user_email='archivematica system',
                reason_for_deletion='All files in Transfer are now in AIPs.'
            )
            elasticSearchFunctions.remove_transfer_files(client, transfer_uuid)

    # DSPACE HANDLE TO ARCHIVESSPACE
    dspace_handle_to_archivesspace(sip_uuid)

    try:
        run_report(sip_uuid)
    except Exception as err:
        # Do our best effort but don't interrupt the script.
        logger.error('The job email report could not be sent: %s',
                     err, exc_info=True)
        pass

    # POST-STORE CALLBACK
    storage_service.post_store_aip_callback(sip_uuid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sip_uuid', help='%SIPUUID%')

    args = parser.parse_args()
    sys.exit(post_store_hook(args.sip_uuid))
