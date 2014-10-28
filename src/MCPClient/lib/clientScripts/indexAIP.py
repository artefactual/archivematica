#!/usr/bin/python2 -OO

import ConfigParser
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'
sys.path.append("/usr/share/archivematica/dashboard")
from main.models import UnitVariable

path = "/usr/lib/archivematica/archivematicaCommon"
if path not in sys.path:
    sys.path.append(path)
import elasticSearchFunctions
from executeOrRunSubProcess import executeOrRun
import storageService as storage_service


def extract_mets(mets_path, aip_path):
    """
    Extract a METS file from an AIP, given the relative METS path
    and the path to the compressed AIP.
    """
    output_mets_path = os.path.join('/tmp', os.path.basename(mets_path))
    command = 'atool --cat {aip_path} {mets_path} > {output}'.format(
        aip_path=aip_path, mets_path=mets_path, output=output_mets_path)
    print 'Extracting METS file with:', command
    exit_code, _, _ = executeOrRun("bashScript", command, printing=True)
    if exit_code != 0:
        raise Exception("Error extracting")

    return output_mets_path


def index_aip():
    """ Write AIP information to ElasticSearch. """
    sip_uuid = sys.argv[1]  # %SIPUUID%
    sip_name = sys.argv[2]  # %SIPName%
    aip_path = sys.argv[3]  # %SIPDirectory%%SIPName%-%SIPUUID%.7z
    sip_type = sys.argv[4]  # %SIPType%

    is_uncompressed_aip = os.path.isdir(aip_path)

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
        return 0

    print 'sip_uuid', sip_uuid
    aip_info = storage_service.get_file_info(uuid=sip_uuid)
    print 'aip_info', aip_info
    aip_info = aip_info[0]

    relative_mets_path = os.path.join(
        "data",
        'METS.{}.xml'.format(sip_uuid)
    )

    if is_uncompressed_aip:
        mets_path = os.path.join(aip_path, relative_mets_path)
    else:
        try:
            # The package contains a top-level directory which is named
            # after the SIP; need to check in there for the METS if
            # the AIP path is a compressed file instead of a directory.
            package_mets_path = os.path.join(
                "{}-{}".format(sip_name, sip_uuid),
                relative_mets_path
            )
            mets_path = extract_mets(package_mets_path, aip_path)
        except:
            print >> sys.stderr, "Unable to extract AIP METS from AIP {} (located at {})".format(sip_uuid, aip_path)
            return 1

    # If this is an AIC, find the number of AIP stored in it and index that
    aips_in_aic = None
    if sip_type == "AIC":
        try:
            uv = UnitVariable.objects.get(unittype="SIP",
                                          unituuid=sip_uuid,
                                          variable="AIPsinAIC")
            aips_in_aic = uv.variablevalue
        except UnitVariable.DoesNotExist:
            pass

    elasticSearchFunctions.connect_and_index_aip(
        sip_uuid,
        sip_name,
        aip_info['current_full_path'],
        mets_path,
        size=aip_info['size'],
        aips_in_aic=aips_in_aic)

    if not is_uncompressed_aip:
        os.remove(mets_path)

    return 0


if __name__ == '__main__':
    sys.exit(index_aip())
