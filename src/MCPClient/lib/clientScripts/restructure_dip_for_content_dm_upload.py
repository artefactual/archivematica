#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Mark Jordan <mark2jordan@gmail.com>

import argparse
import collections
import csv
from lxml import etree
import os
import re
import sys

# archivematicaCommon
import archivematicaFunctions
import namespaces as ns


def parseDmdSec(dmdSec, label="[Placeholder title]"):
    """
    Parses a dmdSec into a dict with child tag names and their values

    :param dmdSec: dmdSec elements
    :param label: Default title if not provided. Required by CONTENTdm
    :returns: Dict of {<child element tag>: [<value>, ...]
    """
    # If the dmdSec object is empty (i.e, no DC metadata has been assigned
    # in the dashboard, and there was no metadata.csv or other metadata file
    # in the transfer), return a placeholder title.
    if dmdSec is None:
        return collections.OrderedDict([("title", [label])])
    elementsDict = archivematicaFunctions.OrderedListsDict()

    # If we are dealing with a DOM object representing the Dublin Core metadata,
    # check to see if there is a title (required by CONTENTdm). If not, assign a
    # placeholder title.
    mdType = dmdSec.xpath("mets:mdWrap/@MDTYPE", namespaces=ns.NSMAP)
    if mdType == "DC":
        dcTitlesDom = dmdSec.findall(".//dcterms:title", namespaces=ns.NSMAP)
        if not dcTitlesDom:
            elementsDict["title"] = label

    # Iterate over all descendants and put in the return dict
    # Key is the element's tag name, value is a list of the element's text
    xmldata = dmdSec.find(".//mets:xmlData", namespaces=ns.NSMAP)
    for element in xmldata.iterdescendants():
        tagname = element.tag
        # Strip namespace prefix
        # TODO can tag names be unicode?
        tagname = re.sub(r"{\S+}", "", tagname)  # \S = non whitespace
        if tagname in ("dublincore",):
            continue
        elementsDict[tagname] = (
            element.text or ""
        )  # OrderedListsDict appends to lists as needed

    return collections.OrderedDict(elementsDict)


def getItemCountType(structMap):
    """
    Get whether this is a simple or compound DIP.

    Compound DIPs have metadata attached to directories, simple DIPs have
    metadata attached to files.

    :param structMap: structMap element from the METS file
    :return: String 'simple', 'compound-dirs' or 'compound-files'
    """
    divs_with_dmdsecs = structMap.findall(".//mets:div[@DMDID]", namespaces=ns.NSMAP)
    # If any are TYPE Directory, then it is compound
    if any([e.get("TYPE") == "Directory" for e in divs_with_dmdsecs]):
        # If all are TYPE Directory then it is bulk
        if all([e.get("TYPE") == "Directory" for e in divs_with_dmdsecs]):
            return "compound-dirs"
        else:
            return "compound-files"
    else:
        return "simple"


def splitDmdSecs(job, dmdSecs):
    """
    Given a group of two dmdSecs, split them out.

    The 'dc' key will be a dmdSec with a MDTYPE='DC' and the 'nonDc' key will be
    a dmdSec with a MDTYPE='OTHER'. Both default to None.

    :param dmdSecs: 1- or 2-tuple of dmdSecs
    :return: Dict with {'dc': <dmdSec or None>, 'nonDc': <dmdSec or None>}
    """
    lenDmdSecs = len(dmdSecs)
    dmdSecPair = {"dc": None, "nonDc": None}
    if lenDmdSecs > 2:
        job.pyprint("Error splitting dmdSecs, more than 2 provided", file=sys.stderr)
        return dmdSecPair
    for dmdSec in dmdSecs:
        mdWrap = dmdSec.find("mets:mdWrap", namespaces=ns.NSMAP)
        if mdWrap.get("MDTYPE") == "OTHER":
            dmdSecPair["nonDc"] = parseDmdSec(dmdSec)
        if mdWrap.get("MDTYPE") == "DC":
            dmdSecPair["dc"] = parseDmdSec(dmdSec)
    if lenDmdSecs == 0:
        # If dmdSecs is empty, let parseDcXML() assign a placeholder title in dcMetadata.
        dmdSecPair["dc"] = parseDmdSec(None)

    return dmdSecPair


def addAipUuidToDcMetadata(dipUuid, dcMetadata):
    """
    Add the AIP UUID to the DC metadata.

    :param dipUuid: UUID of the AIP to add as the identifier.
    :param dcMetadata: Metadata dict to add identifier to, or None.
    """
    if not dcMetadata:
        return None
    if "identifier" not in dcMetadata:
        dcMetadata["identifier"] = [dipUuid]
    else:
        dcMetadata["identifier"].append(dipUuid)
    return dcMetadata


def generate_project_client_package(
    job, output_dir, package_type, structmap, dmdsecs, dipuuid
):
    """
    Generates a simple.txt or compound.txt from the METS of a DIP

    :param output_dir: Path to directory for simple/compound.txt
    :param structmap: structMap element from the METS (Preparse somehow?)
    :param dmdsecs: Dict of {<DMDID>: OrderedDict{column name: value} or <dmdSec element>? }
    :param dipuuid: UUID of the DIP
    """
    job.pyprint("DIP UUID:", dipuuid)

    if "compound" in package_type:
        csv_path = os.path.join(output_dir, "compound.txt")
    else:
        csv_path = os.path.join(output_dir, "simple.txt")

    job.pyprint("Package type:", package_type)
    job.pyprint("Path to the output tabfile", csv_path)

    divs_with_dmdsecs = structmap.findall(".//mets:div[@DMDID]", namespaces=ns.NSMAP)
    with open(csv_path, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter="\t")

        # Iterate through every div and create a row for each
        csv_header_ref = None
        for div in divs_with_dmdsecs:
            # Find associated dmdSecs
            dmdids = div.get("DMDID").split()
            # Take nonDC dmdSec, fallback to DC dmdSec
            dmdsecpair = splitDmdSecs(job, [dmdsecs[dmdid] for dmdid in dmdids])
            dmdsecpair["dc"] = addAipUuidToDcMetadata(dipuuid, dmdsecpair["dc"])
            metadata = dmdsecpair["nonDc"] or dmdsecpair["dc"]
            # Skip dmdSecs without metadata
            if not metadata:
                continue
            # Create csv_header and csv_values from the dmdSec metadata
            csv_header = []
            csv_values = []
            for header, value in metadata.items():
                csv_header.append(header)
                value = "; ".join(value).replace("\r", "").replace("\n", "")
                csv_values.append(archivematicaFunctions.unicodeToStr(value))

            # Add AIP UUID
            csv_header.append("AIP UUID")
            csv_values.append(dipuuid)

            # Add file UUID
            csv_header.append("file UUID")
            if "dirs" in package_type:
                # Directories have no file UUID
                csv_values.append("")
            else:
                file_uuid = ""
                fptr = div.find("mets:fptr", namespaces=ns.NSMAP)
                # Only files have fptrs as direct children
                if fptr is not None:
                    # File UUID is last 36 characters of FILEID
                    file_uuid = fptr.get("FILEID")[-36:]
                csv_values.append(file_uuid)

            # Add file or directory name
            name = div.attrib["LABEL"]  # Fallback if LABEL doesn't exist?
            if "dirs" in package_type:
                csv_header.insert(0, "Directory name")
                csv_values.insert(0, name)
            else:
                csv_header.append("Filename")
                csv_values.append(name)

            # Compare csv_header, if diff ERROR (first time set, write to file)
            if csv_header_ref and csv_header_ref != csv_header:
                job.pyprint(
                    "ERROR headers differ,",
                    csv_path,
                    "almost certainly invalid",
                    file=sys.stderr,
                )
                job.pyprint("Reference header:", csv_header_ref, file=sys.stderr)
                job.pyprint("Differing header:", csv_header, file=sys.stderr)
                return 1
            # If first time through, write out header
            if not csv_header_ref:
                csv_header_ref = csv_header
                writer.writerow(csv_header_ref)
                job.pyprint("Tabfile header:", csv_header)
            # Write csv_row
            writer.writerow(csv_values)
            job.pyprint("Values:", csv_values)
    return 0


def call(jobs):
    parser = argparse.ArgumentParser(description="restructure")
    parser.add_argument(
        "--uuid", action="store", dest="uuid", metavar="UUID", help="%SIPUUID%"
    )
    parser.add_argument(
        "--dipDir",
        action="store",
        dest="dipDir",
        metavar="dipDir",
        help="%SIPDirectory%",
    )

    for job in jobs:
        with job.JobContext():
            args = parser.parse_args(job.args[1:])

            # Perform some preliminary validation on the argument values.
            if not os.path.isdir(args.dipDir):
                job.pyprint("Can't find", args.dipDir, ", exiting.")
                job.set_status(1)
                continue

            # Read and parse the METS file.
            metsFile = os.path.join(args.dipDir, "METS." + args.uuid + ".xml")
            root = etree.parse(metsFile)

            # If there is a user-submitted structMap (i.e., len(structMapts) is 2, use that one.
            # QUESTION why not use physical structMap always?
            structMaps = root.findall("mets:structMap", namespaces=ns.NSMAP)
            archivematica_structmap = structMaps[0]
            if len(structMaps) == 2:
                itemCountType = getItemCountType(structMaps[1])
            else:
                itemCountType = getItemCountType(archivematica_structmap)

            # Get the dmdSec nodes from the METS file.
            dmdsecs = {
                e.get("ID"): e for e in root.findall("mets:dmdSec", namespaces=ns.NSMAP)
            }

            job.set_status(
                generate_project_client_package(
                    job,
                    os.path.join(args.dipDir, "objects"),
                    itemCountType,
                    archivematica_structmap,
                    dmdsecs,
                    args.uuid,
                )
            )
