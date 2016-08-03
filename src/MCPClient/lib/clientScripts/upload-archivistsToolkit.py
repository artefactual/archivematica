#!/usr/bin/env python2

# author: jhs
# created: 2013-01-28
# project: Rockefeller Archivematica - Archivists Toolkit Integration

# notes: this script creates a sql script, that can be run against an AT database
#        it will insert digital object records into AT for existing Archival Descriptions objects
#
# inputs:  requires information about the AT database, and the location of the DIP, plus some metadata supplied by the user
#
# first version of this script gets the input from prompts, next version will get it from MCP db.
#
# example usage:
#
# python at_import.py --host=localhost --port=3306 --dbname="ATTEST" --dbuser=ATuser --dbpass=hello --dip_location="/home/jhs/dip" --dip_name=mydip --atuser=myuser --use_statement="Image-Service" --uri_prefix="http://www.rockarch.org/"
#

from __future__ import print_function
import argparse
import logging
import os
import sys

# archivematicaCommon
from custom_handlers import GroupWriteRotatingFileHandler
from xml2obj import mets_file

# dashboard
from main.models import AtkDIPObjectResourcePairing

# external
from agentarchives.atk import ArchivistsToolkitClient

# global variables
testMode = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('archivematica.mcp.client')
logger.addHandler(logging.NullHandler())
logger.addHandler(GroupWriteRotatingFileHandler('/var/log/archivematica/at_upload.log', mode='a'))


def recursive_file_gen(mydir):
    for root, dirs, files in os.walk(mydir):
        for file in files:
            yield os.path.join(root, file)


def get_user_input():
    print("Archivematica import to AT script")
    print("Welcome\n")
    atdbhost = raw_input("AT database hostname:")
    atdbport = raw_input("AT database port:")
    atdbuser = raw_input("AT database user name:")
    atpass = raw_input("AT database user password:")
    atuser = raw_input("AT username:")
    atdb = raw_input("AT database name:")

    dip_location = raw_input("Location of DIP:")
    dip_name = raw_input("Name of DIP:")

    object_type = raw_input("Object Type:")
    ead_actuate = raw_input("EAD Actuate:")
    ead_show = raw_input("EAD Show:")
    use_statement = raw_input("Use Statement:")

    uri_prefix = raw_input("prefix for uri:")
    return atdbhost, atdbport, atdbuser, atpass, atdb, dip_location, dip_name, atuser, object_type, ead_actuate, ead_show, use_statement, uri_prefix


def get_files_from_dip(dip_location, dip_name, dip_uuid):
    # need to find files in objects dir of dip:
    # go to dipLocation/dipName/objects
    # get a directory listing
    # for each item, set fileName and go
    try:
        mydir = dip_location + "objects/"
        mylist = list(recursive_file_gen(mydir))

        if len(mylist) > 0:
            return mylist
        else:
            logger.error("no files in " + mydir)
            raise ValueError("cannot find dip")
            exit(2)
    except Exception:
        raise
        exit(3)


def get_pairs(dip_uuid):
    # make a set of pairs from pairs table
    return {pair.fileuuid: {'rid': pair.resourceid, 'rcid': pair.resourceComponentId}
            for pair in AtkDIPObjectResourcePairing.objects.filter(dipuuid=dip_uuid)}


def delete_pairs(dip_uuid):
    AtkDIPObjectResourcePairing.objects.filter(dipuuid=dip_uuid).delete()


def upload_to_atk(mylist, atuser, ead_actuate, ead_show, object_type, use_statement, uri_prefix, dip_uuid, access_conditions, use_conditions, restrictions, dip_location):
    logger.info("inputs: actuate '{}' show '{}' type '{}'  use_statement '{}' use_conditions '{}'".format(ead_actuate, ead_show, object_type, use_statement, use_conditions))
    if not uri_prefix.endswith('/'):
        uri_prefix += '/'

    # get mets object if needed
    mets = None
    if restrictions == 'premis' or len(access_conditions) == 0 or len(use_conditions) == 0:
        try:
            logger.debug("looking for mets: {}".format(dip_uuid))
            mets_source = dip_location + 'METS.' + dip_uuid + '.xml'
            mets = mets_file(mets_source)
            logger.debug("found mets file")
        except Exception:
            raise
            exit(4)

    client = ArchivistsToolkitClient(args.atdbhost, args.atdbuser, args.atdbpass, args.atdb)

    pairs = get_pairs(dip_uuid)
    # TODO test to make sure we got some pairs

    for f in mylist:
        logger.info('using ' + f)
        file_name = os.path.basename(f)
        logger.info('file_name is ' + file_name)
        uuid = file_name[0:36]
        access_restrictions = None
        access_rightsGrantedNote = None
        use_restrictions = None
        use_rightsGrantedNote = None
        if mets and mets[uuid]:
            # get premis info from mets
            for premis in mets[uuid]['premis']:
                logger.debug("{} rights = {}, note={}".format(premis, mets[uuid]['premis'][premis]['restriction'],mets[uuid]['premis'][premis]['rightsGrantedNote']))
                if premis == 'disseminate':
                    access_restrictions = mets[uuid]['premis']['disseminate']['restriction']
                    access_rightsGrantedNote = mets[uuid]['premis']['disseminate']['rightsGrantedNote']
                if premis == 'publish':
                    use_restrictions = mets[uuid]['premis']['publish']['restriction']
                    use_rightsGrantedNote = mets[uuid]['premis']['publish']['rightsGrantedNote']
        logger.debug("determine restrictions")
        # determine restrictions
        if restrictions == 'no':
            restrictions_apply = False
        elif restrictions == 'yes':
            restrictions_apply = True
            ead_actuate = "none"
            ead_show = "none"
        elif restrictions == 'premis':
            logger.debug("premis restrictions")
            if access_restrictions == 'Allow' and use_restrictions == 'Allow':
                restrictions_apply = False
            else:
                restrictions_apply = True
                ead_actuate = "none"
                ead_show = "none"

        if len(use_conditions) == 0 or restrictions == 'premis':
            if use_rightsGrantedNote:
                use_conditions = use_rightsGrantedNote

        if len(access_conditions) == 0 or restrictions == 'premis':
            if access_rightsGrantedNote:
                access_conditions = access_rightsGrantedNote

        file_uri = uri_prefix + file_name

        if uuid in pairs:
            resource_id = pairs[uuid]['rcid'] if pairs[uuid]['rcid'] > 0 else pairs[uuid]['rid']
            client.add_digital_object(resource_id,
                                      uuid,
                                      uri=file_uri,
                                      restricted=restrictions_apply,
                                      xlink_actuate=ead_actuate,
                                      xlink_show=ead_show,
                                      location_of_originals=dip_uuid,
                                      inherit_dates=True)

    delete_pairs(dip_uuid)
    logger.info("completed upload successfully")

if __name__ == '__main__':

    RESTRICTIONS_CHOICES = ['yes', 'no', 'premis']
    EAD_SHOW_CHOICES = ['embed', 'new', 'none', 'other', 'replace']
    EAD_ACTUATE_CHOICES = ['none', 'onLoad', 'other', 'onRequest']

    parser = argparse.ArgumentParser(description="A program to take digital objects from a DIP and upload them to an archivists toolkit db")
    parser.add_argument('--host', default="localhost", dest="atdbhost",
                        metavar="host", help="hostname or ip of archivists toolkit db")
    parser.add_argument('--port', type=int, default=3306, dest='atdbport',
                        metavar="port", help="port used by archivists toolkit mysql db")
    parser.add_argument('--dbname', dest='atdb', metavar="db",
                        help="name of mysql database used by archivists toolkit")
    parser.add_argument('--dbuser', dest='atdbuser', metavar="db user")
    parser.add_argument('--dbpass', dest='atdbpass', metavar="db password")
    parser.add_argument('--dip_location', metavar="dip location")
    parser.add_argument('--dip_name', metavar="dip name")
    parser.add_argument('--dip_uuid', metavar="dip uuid")
    parser.add_argument('--atuser', metavar="at user")
    parser.add_argument('--restrictions', metavar="restrictions apply", default="premis", choices=RESTRICTIONS_CHOICES)
    parser.add_argument('--object_type', metavar="object type", default="")
    parser.add_argument('--ead_actuate', metavar="ead actuate", default="onRequest", choices=EAD_ACTUATE_CHOICES)
    parser.add_argument('--ead_show', metavar="ead show", default="new", choices=EAD_SHOW_CHOICES)
    parser.add_argument('--use_statement', metavar="use statement")
    parser.add_argument('--uri_prefix', metavar="uri prefix")
    parser.add_argument('--access_conditions', metavar="conditions governing access", default="")
    parser.add_argument('--use_conditions', metavar="conditions governing use", default="")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
    args = parser.parse_args()
    if not args.atdb:
        get_user_input()

    try:
        mylist = get_files_from_dip(args.dip_location, args.dip_name, args.dip_uuid)
        upload_to_atk(mylist, args.atuser, args.ead_actuate, args.ead_show, args.object_type, args.use_statement, args.uri_prefix, args.dip_uuid, args.access_conditions, args.use_conditions, args.restrictions, args.dip_location)

    except Exception:
        logging.exception("Unable to upload DIPs to Archivist's Toolkit")
        sys.exit(1)
