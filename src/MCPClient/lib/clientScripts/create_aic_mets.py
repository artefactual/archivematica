#!/usr/bin/env python2

import argparse
from lxml import etree
from lxml.builder import ElementMaker
import os
import re
import uuid

import django
from django.db import transaction

django.setup()
# dashboard
from django.utils import timezone
from main.models import UnitVariable

import create_mets_v2

# archivematicaCommon
import databaseFunctions
import fileOperations
import namespaces as ns
import storageService as storage_service


def get_aip_info(aic_dir, job):
    """ Get AIP UUID, name and labels from objects directory and METS file. """
    aips = []
    aic_dir = os.path.join(aic_dir, "objects")
    # Parse out AIP names and UUIDs
    # The only contents of the folder should be a bunch of files whose filenames
    # are AIP UUIDs, and the contents are the AIP name.
    uuid_regex = (
        r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
    )
    files = [
        d
        for d in os.listdir(aic_dir)
        if os.path.isfile(os.path.join(aic_dir, d)) and re.match(uuid_regex, d)
    ]
    for filename in files:
        file_path = os.path.join(aic_dir, filename)
        with open(file_path, "r") as f:
            aip_name = f.readline()
        os.remove(file_path)
        aips.append({"name": aip_name, "uuid": filename})

    # Fetch the METS file and parse out the Dublic Core metadata with the label
    for aip in aips:
        mets_in_aip = "{aip_name}-{aip_uuid}/data/METS.{aip_uuid}.xml".format(
            aip_name=aip["name"], aip_uuid=aip["uuid"]
        )
        mets_path = os.path.join(aic_dir, "METS.{}.xml".format(aip["uuid"]))
        storage_service.extract_file(aip["uuid"], mets_in_aip, mets_path)

        root = etree.parse(mets_path)
        # Title may be namespaced as dc: or dcterms: depending on version
        aip["label"] = (
            root.findtext(
                "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore/dc:title",
                namespaces=ns.NSMAP,
            )
            or root.findtext(
                "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore/dcterms:title",
                namespaces=ns.NSMAP,
            )
            or ""
        )

        os.remove(mets_path)

    job.pyprint("AIP info:", aips)
    return aips


def create_mets_file(aic, aips, job):
    """ Create AIC METS file with AIP information. """

    # Prepare constants
    nsmap = {"mets": ns.metsNS, "xlink": ns.xlinkNS, "xsi": ns.xsiNS}
    now = timezone.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Set up structure
    E = ElementMaker(namespace=ns.metsNS, nsmap=nsmap)
    mets = E.mets(
        E.metsHdr(CREATEDATE=now),
        E.dmdSec(E.mdWrap(E.xmlData(), MDTYPE="DC"), ID="dmdSec_1"),  # mdWrap  # dmdSec
        E.fileSec(E.fileGrp()),
        E.structMap(
            E.div(TYPE="Archival Information Collection", DMDID="dmdSec_1"),
            TYPE="logical",  # structMap
        ),
    )
    mets.attrib[
        "{{{ns}}}schemaLocation".format(ns=nsmap["xsi"])
    ] = "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version1121/mets.xsd"

    # Add Dublin Core info
    xml_data = mets.find("mets:dmdSec/mets:mdWrap/mets:xmlData", namespaces=ns.NSMAP)
    dublincore = create_mets_v2.getDublinCore(
        create_mets_v2.SIPMetadataAppliesToType, aic["uuid"]
    )
    # Add <extent> with number of AIPs
    extent = etree.SubElement(dublincore, ns.dctermsBNS + "extent")
    extent.text = "{} AIPs".format(len(aips))
    xml_data.append(dublincore)

    # Add elements for each AIP
    file_grp = mets.find("mets:fileSec/mets:fileGrp", namespaces=ns.NSMAP)
    struct_div = mets.find("mets:structMap/mets:div", namespaces=ns.NSMAP)
    for aip in aips:
        file_id = "{name}-{uuid}".format(name=aip["name"], uuid=aip["uuid"])
        etree.SubElement(file_grp, ns.metsBNS + "file", ID=file_id)

        label = aip["label"] or aip["name"]
        div = etree.SubElement(struct_div, ns.metsBNS + "div", LABEL=label)
        etree.SubElement(div, ns.metsBNS + "fptr", FILEID=file_id)

    job.pyprint(etree.tostring(mets, pretty_print=True))

    # Write out the file
    file_uuid = str(uuid.uuid4())
    basename = os.path.join("metadata", "METS.{}.xml".format(file_uuid))
    filename = os.path.join(aic["dir"], basename)
    with open(filename, "w") as f:
        f.write(
            etree.tostring(
                mets, pretty_print=True, xml_declaration=True, encoding="utf-8"
            )
        )
    fileOperations.addFileToSIP(
        filePathRelativeToSIP="%SIPDirectory%" + basename,
        fileUUID=file_uuid,
        sipUUID=aic["uuid"],
        taskUUID=str(uuid.uuid4()),  # Unsure what should go here
        date=now,
        sourceType="aip creation",
        use="metadata",
    )
    # To make this work with the createMETS2 (for SIPs)
    databaseFunctions.insertIntoDerivations(file_uuid, file_uuid)

    # Insert the count of AIPs in the AIC into UnitVariables, so it can be
    # indexed later
    UnitVariable.objects.create(
        unittype="SIP",
        unituuid=aic["uuid"],
        variable="AIPsinAIC",
        variablevalue=str(len(aips)),
    )


def create_aic_mets(aic_uuid, aic_dir, job):
    aips = get_aip_info(aic_dir, job)
    aic = {"dir": aic_dir, "uuid": aic_uuid}
    create_mets_file(aic, aips, job)


def call(jobs):
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("aic_uuid", action="store", type=str, help="%SIPUUID%")
    parser.add_argument("aic_dir", action="store", type=str, help="%SIPDirectory%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                create_aic_mets(args.aic_uuid, args.aic_dir, job)
