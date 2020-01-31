#!/usr/bin/env python2

import argparse
import logging
import os

from main.models import ArchivesSpaceDIPObjectResourcePairing, File
from fpr.models import FormatVersion

# archivematicaCommon
from xml2obj import mets_file

# Third party dependencies, alphabetical by import source
from agentarchives.archivesspace import ArchivesSpaceClient
from agentarchives.archivesspace import ArchivesSpaceError

# initialize Django (required for Django 1.7)
import django
import scandir

django.setup()
from django.db import transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.addHandler(logging.FileHandler("/tmp/as_upload.log", mode="a"))


def recursive_file_gen(mydir):
    for root, dirs, files in scandir.walk(mydir):
        for file in files:
            yield os.path.join(root, file)


def get_files_from_dip(dip_location):
    # need to find files in objects dir of dip:
    # go to dipLocation/objects
    # get a directory listing
    # for each item, set fileName and go
    try:
        # remove trailing slash
        if dip_location != os.path.sep:
            dip_location = dip_location.rstrip(os.path.sep)
        mydir = os.path.join(dip_location, "objects")
        mylist = list(recursive_file_gen(mydir))

        if len(mylist) > 0:
            return mylist
        else:
            logger.error("no files in " + mydir)
            raise ValueError("cannot find dip")
    except Exception:
        raise


def get_pairs(dip_uuid):
    return {
        pair.fileuuid: pair.resourceid
        for pair in ArchivesSpaceDIPObjectResourcePairing.objects.filter(
            dipuuid=dip_uuid
        )
    }


def delete_pairs(dip_uuid):
    ArchivesSpaceDIPObjectResourcePairing.objects.filter(dipuuid=dip_uuid).delete()


def upload_to_archivesspace(
    files,
    client,
    xlink_show,
    xlink_actuate,
    object_type,
    use_statement,
    uri,
    dip_uuid,
    access_conditions,
    use_conditions,
    restrictions,
    dip_location,
    inherit_notes,
):

    if not uri.endswith("/"):
        uri += "/"
    pairs = get_pairs(dip_uuid)

    # get mets object if needed
    mets = None
    if (
        restrictions == "premis"
        or len(access_conditions) == 0
        or len(use_conditions) == 0
    ):
        logger.debug("Looking for mets: {}".format(dip_uuid))
        mets_source = os.path.join(dip_location, "METS.{}.xml".format(dip_uuid))
        mets = mets_file(mets_source)
        logger.debug("Found mets file at path: {}".format(mets_source))

    all_files_paired_successfully = True
    for f in files:
        file_name = os.path.basename(f)
        uuid = file_name[0:36]

        if uuid not in pairs:
            logger.error("Skipping file {} ({}) - no pairing found".format(f, uuid))
            all_files_paired_successfully = False
            continue

        as_resource = pairs[uuid]

        access_restrictions = None
        access_rightsGrantedNote = None
        use_restrictions = None
        use_rightsGrantedNote = None

        if mets and mets[uuid]:
            # get premis info from mets
            for premis in mets[uuid]["premis"]:
                logger.debug(
                    "{} rights = {}, note={}".format(
                        premis,
                        mets[uuid]["premis"][premis]["restriction"],
                        mets[uuid]["premis"][premis]["rightsGrantedNote"],
                    )
                )
                if premis == "disseminate":
                    access_restrictions = mets[uuid]["premis"]["disseminate"][
                        "restriction"
                    ]
                    access_rightsGrantedNote = mets[uuid]["premis"]["disseminate"][
                        "rightsGrantedNote"
                    ]
                if premis == "publish":
                    use_restrictions = mets[uuid]["premis"]["publish"]["restriction"]
                    use_rightsGrantedNote = mets[uuid]["premis"]["publish"][
                        "rightsGrantedNote"
                    ]

        # determine restrictions
        restrictions_apply = False
        if restrictions == "yes":
            restrictions_apply = True
            xlink_actuate = "none"
            xlink_show = "none"
        elif restrictions == "premis":
            logger.debug("premis restrictions")
            if access_restrictions == "Allow" and use_restrictions == "Allow":
                restrictions_apply = False
            else:
                restrictions_apply = True
                xlink_actuate = "none"
                xlink_show = "none"

        if len(use_conditions) == 0 or restrictions == "premis":
            if use_rightsGrantedNote:
                use_conditions = use_rightsGrantedNote

        if len(access_conditions) == 0 or restrictions == "premis":
            if access_rightsGrantedNote:
                access_conditions = access_rightsGrantedNote

        # Get file & format info
        # Client wants access copy info

        original_name = ""
        # Get file & format info
        try:
            fv = FormatVersion.objects.get(fileformatversion__file_uuid=uuid)
            format_version = fv.description
            format_name = fv.format.description
        except FormatVersion.DoesNotExist:
            format_name = format_version = None

        # Client wants access copy info
        try:
            original_file = File.objects.get(filegrpuse="original", uuid=uuid)
        except (File.DoesNotExist, File.MultipleObjectsReturned):
            original_name = ""
            size = format_name = format_version = None
        else:
            # Set some variables based on the original, we will override most
            # of these if there is an access derivative
            size = os.path.getsize(f)
            original_name = os.path.basename(original_file.originallocation)
        try:
            access_file = File.objects.get(
                filegrpuse="access", original_file_set__source_file=uuid
            )
        except (File.DoesNotExist, File.MultipleObjectsReturned):
            # Just use original file info
            pass
        else:
            # HACK remove DIP from the path because create DIP doesn't
            access_file_path = access_file.currentlocation.replace(
                "%SIPDirectory%DIP/", dip_location
            )
            size = os.path.getsize(access_file_path)

        # HACK map the format version to ArchivesSpace's fixed list of formats it accepts.
        as_formats = {
            "Audio Interchange File Format": "aiff",
            "Audio/Video Interleaved": "avi",
            "Graphics Interchange Format": "gif",
            "JPEG": "jpeg",
            "MPEG Audio": "mp3",
            "PDF": "pdf",
            "Tagged Image File Format": "tiff",
            "Plain Text": "txt",
        }
        if format_name is not None:
            format_name = as_formats.get(format_name)

        logger.info(
            "Uploading {} to ArchivesSpace record {}".format(file_name, as_resource)
        )
        try:
            client.add_digital_object(
                parent_archival_object=as_resource,
                identifier=uuid,
                # TODO: fetch a title from DC?
                #       Use the title of the parent record?
                title=original_name,
                uri=uri + file_name,
                location_of_originals=dip_uuid,
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
                inherit_notes=inherit_notes,
            )
        except ArchivesSpaceError as error:

            logger.error(
                "Could not upload {} to ArchivesSpace record {}. Error: {}".format(
                    file_name, as_resource, str(error)
                )
            )
            all_files_paired_successfully = False

        delete_pairs(dip_uuid)

    return all_files_paired_successfully


def get_parser(RESTRICTIONS_CHOICES, EAD_ACTUATE_CHOICES, EAD_SHOW_CHOICES):
    parser = argparse.ArgumentParser(
        description="A program to take digital objects from a DIP and upload them to an ArchivesSpace db"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8089",
        dest="base_url",
        metavar="base_url",
        help="Hostname of ArchivesSpace",
    )
    parser.add_argument("--user", dest="user", help="Administrative user")
    parser.add_argument("--passwd", dest="passwd", help="Administrative user password")
    parser.add_argument("--dip_location", help="DIP location")
    parser.add_argument("--dip_name", help="DIP name")
    parser.add_argument("--dip_uuid", help="DIP UUID")
    parser.add_argument(
        "--restrictions",
        help="Restrictions apply",
        default="premis",
        choices=RESTRICTIONS_CHOICES,
    )
    parser.add_argument("--object_type", help="object type", default="")
    parser.add_argument(
        "--xlink_actuate",
        help="XLink actuate",
        default="onRequest",
        choices=EAD_ACTUATE_CHOICES,
    )
    parser.add_argument(
        "--xlink_show", help="XLink show", default="new", choices=EAD_SHOW_CHOICES
    )
    parser.add_argument("--use_statement", help="USE statement")
    parser.add_argument("--uri_prefix", help="URI prefix")
    parser.add_argument(
        "--access_conditions", help="Conditions governing access", default=""
    )
    parser.add_argument("--use_conditions", help="Conditions governing use", default="")
    parser.add_argument(
        "--inherit_notes",
        help="Inherit digital object notes from the parent component",
        default="no",
        type=str,
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    return parser


def call(jobs):
    RESTRICTIONS_CHOICES = ["yes", "no", "premis"]
    EAD_SHOW_CHOICES = ["embed", "new", "none", "other", "replace"]
    EAD_ACTUATE_CHOICES = ["none", "onLoad", "other", "onRequest"]
    INHERIT_NOTES_CHOICES = ["yes", "y", "true", "1"]

    parser = get_parser(RESTRICTIONS_CHOICES, EAD_ACTUATE_CHOICES, EAD_SHOW_CHOICES)

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])

                args.inherit_notes = args.inherit_notes.lower() in INHERIT_NOTES_CHOICES

                client = ArchivesSpaceClient(
                    host=args.base_url, user=args.user, passwd=args.passwd
                )

                try:
                    files = get_files_from_dip(args.dip_location)
                except ValueError:
                    job.set_status(2)
                    continue
                except Exception:
                    job.set_status(3)
                    continue
                if upload_to_archivesspace(
                    files,
                    client,
                    args.xlink_show,
                    args.xlink_actuate,
                    args.object_type,
                    args.use_statement,
                    args.uri_prefix,
                    args.dip_uuid,
                    args.access_conditions,
                    args.use_conditions,
                    args.restrictions,
                    args.dip_location,
                    args.inherit_notes,
                ):
                    job.set_status(0)
                else:
                    job.set_status(2)
