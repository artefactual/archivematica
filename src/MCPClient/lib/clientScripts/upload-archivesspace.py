#!/usr/bin/env python2

import argparse
import logging
import os

from main.models import ArchivesSpaceDIPObjectResourcePairing, File
from fpr.models import FormatVersion

# archivematicaCommon
from archivesspace.client import ArchivesSpaceClient
from elasticSearchFunctions import getDashboardUUID
from xml2obj import mets_file

# initialize Django (required for Django 1.7)
import django
django.setup()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.addHandler(logging.FileHandler('/tmp/as_upload.log', mode='a'))


def recursive_file_gen(mydir):
    for root, dirs, files in os.walk(mydir):
        for file in files:
            yield os.path.join(root, file)


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
    return {pair.fileuuid: pair.resourceid for pair in ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=dip_uuid)}


def delete_pairs(dip_uuid):
    ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=dip_uuid).delete()


def upload_to_archivesspace(files, client, xlink_show, xlink_actuate, object_type, use_statement, uri, dip_uuid, access_conditions, use_conditions, restrictions, dip_location):

    if not uri.endswith('/'):
        uri += '/'
    pairs = get_pairs(dip_uuid)
    dashboard_uuid = getDashboardUUID()

    # get mets object if needed
    mets = None
    if restrictions == 'premis' or len(access_conditions) == 0 or len(use_conditions) == 0:
        logger.debug("Looking for mets: {}".format(dip_uuid))
        mets_source = dip_location + 'METS.' + dip_uuid + '.xml'
        mets = mets_file(mets_source)
        logger.debug("Found mets file at path: {}".format(mets_source))

    for f in files:
        file_name = os.path.basename(f)
        uuid = file_name[0:36]

        if uuid not in pairs:
            logger.warning("Skipping file {} ({}) - no pairing found".format(f, uuid))
            continue

        as_resource = pairs[uuid]

        access_restrictions = None
        access_rightsGrantedNote = None
        use_restrictions = None
        use_rightsGrantedNote = None

        if mets and mets[uuid]:
            # get premis info from mets
            for premis in mets[uuid]['premis']:
                logger.debug("{} rights = {}, note={}".format(premis, mets[uuid]['premis'][premis]['restriction'], mets[uuid]['premis'][premis]['rightsGrantedNote']))
                if premis == 'disseminate':
                    access_restrictions = mets[uuid]['premis']['disseminate']['restriction']
                    access_rightsGrantedNote = mets[uuid]['premis']['disseminate']['rightsGrantedNote']
                if premis == 'publish':
                    use_restrictions = mets[uuid]['premis']['publish']['restriction']
                    use_rightsGrantedNote = mets[uuid]['premis']['publish']['rightsGrantedNote']

        # determine restrictions
        if restrictions == 'no':
            restrictions_apply = False
        elif restrictions == 'yes':
            restrictions_apply = True
            xlink_actuate = "none"
            xlink_show = "none"
        elif restrictions == 'premis':
            logger.debug("premis restrictions")
            if access_restrictions == 'Allow' and use_restrictions == 'Allow':
                restrictions_apply = False
            else:
                restrictions_apply = True
                xlink_actuate = "none"
                xlink_show = "none"

        if len(use_conditions) == 0 or restrictions == 'premis':
            if use_rightsGrantedNote:
                use_conditions = use_rightsGrantedNote

        if len(access_conditions) == 0 or restrictions == 'premis':
            if access_rightsGrantedNote:
                access_conditions = access_rightsGrantedNote

        # Get file & format info
        # Client wants access copy info
        try:
            access_file = File.objects.get(
                filegrpuse='access',
                original_file_set__source_file=uuid
            )
        except (File.DoesNotExist, File.MultipleObjectsReturned):
            size = format_name = format_version = None
        else:
            # HACK remove DIP from the path because create DIP doesn't
            access_file_path = access_file.currentlocation.replace('%SIPDirectory%DIP/', dip_location)
            size = os.path.getsize(access_file_path)
            fv = FormatVersion.objects.get(fileformatversion__file_uuid=access_file.uuid)
            format_version = fv.description
            format_name = fv.format.description

            # HACK map the format version to ArchivesSpace's fixed list of formats it accepts.
            as_formats = {
                'Audio Interchange File Format': 'aiff',
                'Audio/Video Interleaved': 'avi',
                'Graphics Interchange Format': 'gif',
                'JPEG': 'jpeg',
                'MPEG Audio': 'mp3',
                'PDF': 'pdf',
                'Tagged Image File Format': 'tiff',
                'Plain Text': 'txt',
            }
            format_name = as_formats.get(format_name)

        logger.info("Uploading {} to ArchivesSpace record {}".format(file_name, as_resource))
        client.add_digital_object(as_resource,
                                  dashboard_uuid,
                                  # TODO: fetch a title from DC?
                                  #       Use the title of the parent record?
                                  uri=uri + file_name,
                                  identifier=uuid,
                                  object_type=object_type,
                                  use_statement=use_statement,
                                  xlink_show=xlink_show,
                                  xlink_actuate=xlink_actuate,
                                  restricted=restrictions_apply,
                                  use_conditions=use_conditions,
                                  access_conditions=access_conditions,
                                  size=size,
                                  format_name=format_name,
                                  format_version=format_version,
        )

        delete_pairs(dip_uuid)

if __name__ == '__main__':
    RESTRICTIONS_CHOICES = ['yes', 'no', 'premis']
    EAD_SHOW_CHOICES = ['embed', 'new', 'none', 'other', 'replace']
    EAD_ACTUATE_CHOICES = ['none', 'onLoad', 'other', 'onRequest']

    parser = argparse.ArgumentParser(description="A program to take digital objects from a DIP and upload them to an ArchivesSpace db")
    parser.add_argument('--host', default="localhost", dest="host",
        metavar="host", help="hostname of ArchivesSpace")
    parser.add_argument('--port', type=int, default=8089, dest='port',
        metavar="port", help="Port used by ArchivesSpace backend API")
    parser.add_argument('--user', dest='user', metavar="Administrative user")
    parser.add_argument('--passwd', dest='passwd', metavar="Administrative user password")
    parser.add_argument('--dip_location', metavar="dip location")
    parser.add_argument('--dip_name', metavar="dip name")
    parser.add_argument('--dip_uuid', metavar="dip uuid")
    parser.add_argument('--restrictions', metavar="restrictions apply", default="premis", choices=RESTRICTIONS_CHOICES)
    parser.add_argument('--object_type', metavar="object type", default="")
    parser.add_argument('--xlink_actuate', metavar="xlink actuate", default="onRequest", choices=EAD_ACTUATE_CHOICES)
    parser.add_argument('--xlink_show', metavar="xlink show", default="new", choices=EAD_SHOW_CHOICES)
    parser.add_argument('--use_statement', metavar="use statement")
    parser.add_argument('--uri_prefix', metavar="uri prefix")
    parser.add_argument('--access_conditions', metavar="conditions governing access", default="")
    parser.add_argument('--use_conditions', metavar="conditions governing use", default="")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
    args = parser.parse_args()

    client = ArchivesSpaceClient(host=args.host, user=args.user, passwd=args.passwd)
    files = get_files_from_dip(args.dip_location, args.dip_name, args.dip_uuid)
    upload_to_archivesspace(files, client, args.xlink_show, args.xlink_actuate, args.object_type, args.use_statement, args.uri_prefix, args.dip_uuid, args.access_conditions, args.use_conditions, args.restrictions, args.dip_location)
