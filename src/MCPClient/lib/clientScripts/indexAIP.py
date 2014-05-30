#!/usr/bin/python2 -OO

import ConfigParser
import os
import sys

path = "/usr/lib/archivematica/archivematicaCommon"
if path not in sys.path:
    sys.path.append(path)
import databaseInterface
import elasticSearchFunctions
from executeOrRunSubProcess import executeOrRun
import storageService as storage_service

path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

from main import models

def index_aip():
    """ Write AIP information to ElasticSearch. """
    sip_uuid = sys.argv[1]  # %SIPUUID%
    sip_name = sys.argv[2]  # %SIPName%
    aip_path = sys.argv[3]  # %SIPDirectory%%SIPName%-%SIPUUID%.7z
    sip_type = sys.argv[4]  # %SIPType%

    # Check if ElasticSearch is enabled
    client_config_path = '/etc/archivematica/MCPClient/clientConfig.conf'
    config = ConfigParser.SafeConfigParser()
    config.read(client_config_path)
    elastic_search_disabled = False
    try:
        elastic_search_disabled = config.getboolean(
            'MCPClient', "disableElasticsearchIndexing")
    except ConfigParser.NoOptionError:
        pass
    if elastic_search_disabled:
        print 'Skipping indexing: indexing is currently disabled in {}.'.format(client_config_path)
        return (0)

    print 'sip_uuid', sip_uuid
    aip_info = storage_service.get_file_info(uuid=sip_uuid)
    print 'aip_info', aip_info
    aip_info = aip_info[0]

    # Extract METS file, so Elastic Search can parse it
    zip_mets_path = os.path.join(
        "{}-{}".format(sip_name, sip_uuid),
        "data",
        'METS.{}.xml'.format(sip_uuid))
    mets_path = os.path.join('/tmp', "METS.{}.xml".format(sip_uuid))
    command = 'atool --cat {aip_path} {zip_mets_path} > {mets_path}'.format(
        aip_path=aip_path, zip_mets_path=zip_mets_path, mets_path=mets_path)
    print 'Extracting METS file with:', command
    exit_code, _, _ = executeOrRun("bashScript", command, printing=True)
    if exit_code != 0:
        print >>sys.stderr, "Error extracting"
        sys.exit(1)

    # If this is an AIC, find the number of AIP stored in it and index that
    aips_in_aic = None
    if sip_type == "AIC":
        sql = """SELECT variableValue FROM UnitVariables WHERE unitType='SIP' AND unitUUID='%s' AND variable='AIPsinAIC';""" % (sip_uuid,)
        rows = databaseInterface.queryAllSQL(sql)
        if rows:
            aips_in_aic = rows[0][0]

    elasticSearchFunctions.connect_and_index_aip(
        sip_uuid,
        sip_name,
        aip_info['current_full_path'],
        mets_path,
        size=aip_info['size'],
        aips_in_aic=aips_in_aic)

    os.remove(mets_path)

    # Mark files in this SIP as in an AIP (aip_created)
    file_uuids = models.File.objects.filter(sip=sip_uuid).values_list('uuid', flat=True)
    models.SIPArrange.objects.filter(file_uuid__in=file_uuids).update(aip_created=True)

    # Check if any of component transfers are completely stored
    # TODO Storage service should index AIPs, knows when to update ES
    transfer_uuids = set(models.SIPArrange.objects.filter(file_uuid__in=file_uuids).values_list('transfer_uuid', flat=True))
    for transfer_uuid in transfer_uuids:
        print 'Checking if transfer', transfer_uuid, 'is fully stored...'
        arranged_uuids = set(models.SIPArrange.objects.filter(transfer_uuid=transfer_uuid).filter(aip_created=True).values_list('file_uuid', flat=True))
        backlog_uuids = set(models.File.objects.filter(transfer=transfer_uuid).values_list('uuid', flat=True))
        # If all backlog UUIDs have been arranged
        if arranged_uuids == backlog_uuids:
            print 'Transfer', transfer_uuid, 'fully stored, sending delete request to storage service, deleting from transfer backlog'
            # Submit delete req to SS (not actually delete), remove from ES
            storage_service.request_file_deletion(
                uuid=transfer_uuid,
                user_id=0,
                user_email='archivematica system',
                reason_for_deletion='All files in Transfer are now in AIPs.'
            )
            elasticSearchFunctions.connect_and_remove_sip_transfer_files(transfer_uuid)


if __name__ == '__main__':
    index_aip()
