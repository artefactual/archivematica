#!/usr/bin/env python2
# -*- coding: utf-8 -*-

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

from __future__ import print_function
import argparse
import json
import os
import sys
import uuid

from lxml import etree

import metsrw
from custom_handlers import get_script_logger

logger = get_script_logger("archivematica.mcp.client.dataverse")


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
DISTRBTR = "SP Dataverse Network"
# Mapping from originalFormatLabel to file extension
# Reference for values:
# https://github.com/IQSS/dataverse/blob/4.0.1/src/main/java/MimeTypeDisplay.properties
# https://github.com/IQSS/dataverse/blob/4.0.1/src/main/java/META-INF/mime.types
EXTENSION_MAPPING = {
    "Comma Separated Values": ".csv",
    "MS Excel (XLSX)": ".xlsx",
    "R Data": ".RData",
    "SPSS Portable": ".por",
    "SPSS SAV": ".sav",
    "Stata Binary": ".dta",
    "Stata 13 Binary": ".dta",
    "UNKNOWN": "",
}


def get_ddi_titl_author(j):
    titl_text = authenty_text = None
    for field in j["latestVersion"]["metadataBlocks"]["citation"]["fields"]:
        if field["typeName"] == "title":
            titl_text = field["value"]
        if field["typeName"] == "author":
            authenty_text = field["value"][0]["authorName"]["value"]
    return titl_text, authenty_text


def create_ddi(j):
    """
    Create the DDI dmdSec from JSON information. Returns Element.
    """
    # Get data
    titl_text, authenty_text = get_ddi_titl_author(j)
    agency = j["protocol"]
    idno = j["authority"] + "/" + j["identifier"]
    version_date = j["latestVersion"]["releaseTime"]
    version_type = j["latestVersion"]["versionState"]
    version_num = "{}.{}".format(
        j["latestVersion"]["versionNumber"], j["latestVersion"]["versionMinorNumber"]
    )
    restrctn_text = j["latestVersion"].get("termsOfUse")

    # create XML
    nsmap = {"ddi": "http://www.icpsr.umich.edu/DDI"}
    ddins = "{" + nsmap["ddi"] + "}"
    ddi_root = etree.Element(ddins + "codebook", nsmap=nsmap)
    ddi_root.attrib["version"] = "2.5"

    root_ns = "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
    dv_ns = (
        "http://www.ddialliance.org/Specification/DDI-Codebook/2.5/"
        "XMLSchema/codebook.xsd"
    )
    ddi_root.attrib[root_ns] = dv_ns

    stdydscr = etree.SubElement(ddi_root, ddins + "stdyDscr", nsmap=nsmap)
    citation = etree.SubElement(stdydscr, ddins + "citation", nsmap=nsmap)

    titlstmt = etree.SubElement(citation, ddins + "titlStmt", nsmap=nsmap)
    etree.SubElement(titlstmt, ddins + "titl", nsmap=nsmap).text = titl_text
    etree.SubElement(titlstmt, ddins + "IDNo", agency=agency).text = idno

    rspstmt = etree.SubElement(citation, ddins + "rspStmt")
    etree.SubElement(rspstmt, ddins + "AuthEnty").text = authenty_text

    diststmt = etree.SubElement(citation, ddins + "distStmt")
    etree.SubElement(diststmt, ddins + "distrbtr").text = DISTRBTR

    verstmt = etree.SubElement(citation, ddins + "verStmt")
    etree.SubElement(
        verstmt, ddins + "version", date=version_date, type=version_type
    ).text = version_num

    dataaccs = etree.SubElement(stdydscr, ddins + "dataAccs")
    usestmt = etree.SubElement(dataaccs, ddins + "useStmt")
    etree.SubElement(usestmt, ddins + "restrctn").text = restrctn_text

    return ddi_root


def create_bundle(tabfile_json):
    """
    Creates and returns the metsrw entries for a tabfile's bundle
    """
    # Base name is .tab with suffix stripped
    base_name = tabfile_json["label"][:-4]
    bundle = metsrw.FSEntry(path=base_name, type="Directory")

    # Find original file
    ext = EXTENSION_MAPPING[tabfile_json["dataFile"]["originalFormatLabel"]]
    original_file = metsrw.FSEntry(
        path=base_name + "/" + base_name + ext,
        use="original",
        file_uuid=str(uuid.uuid4()),
        checksumtype="MD5",
        checksum=tabfile_json["dataFile"]["md5"],
    )
    bundle.add_child(original_file)
    if tabfile_json["dataFile"]["originalFormatLabel"] != "R Data":
        # RData derivative
        f = metsrw.FSEntry(
            path=base_name + "/" + base_name + ".RData",
            use="derivative",
            derived_from=original_file,
            file_uuid=str(uuid.uuid4()),
        )
        bundle.add_child(f)

    # Add expected bundle contents
    # FIXME what is the actual path for the files?
    # Tabfile
    f = metsrw.FSEntry(
        path=base_name + "/" + tabfile_json["dataFile"]["filename"],
        use="derivative",
        derived_from=original_file,
        file_uuid=str(uuid.uuid4()),
    )
    f.add_dmdsec(
        md=base_name + "/" + base_name + "-ddi.xml",
        mdtype="DDI",
        mode="mdref",
        label=base_name + "-ddi.xml",
        loctype="OTHER",
        otherloctype="SYSTEM",
    )
    bundle.add_child(f)
    # -ddi.xml
    f = metsrw.FSEntry(
        path=base_name + "/" + base_name + "-ddi.xml",
        use="metadata",
        derived_from=original_file,
        file_uuid=str(uuid.uuid4()),
    )
    bundle.add_child(f)
    # citation - endnote
    f = metsrw.FSEntry(
        path=base_name + "/" + base_name + "citation-endnote.xml",
        use="metadata",
        derived_from=original_file,
        file_uuid=str(uuid.uuid4()),
    )
    bundle.add_child(f)
    # citation - ris
    f = metsrw.FSEntry(
        path=base_name + "/" + base_name + "citation-ris.ris",
        use="metadata",
        derived_from=original_file,
        file_uuid=str(uuid.uuid4()),
    )
    bundle.add_child(f)

    return bundle


def map_dataverse(sip_dir, dataset_md_name="dataset.json",
                  md_path=None, md_name=None):

    # Read JSON
    json_path = os.path.join(sip_dir, "metadata", dataset_md_name)
    logger.info("Metadata directory exists %s", os.path.exists(json_path))
    with open(json_path, "r") as f:
        j = json.load(f)

    # Parse DDI into XML
    ddi_root = create_ddi(j)

    # Create METS
    sip = metsrw.FSEntry(
        path=None, label=get_ddi_titl_author(j)[0], use=None, type="Directory"
    )
    sip.add_dmdsec(md=ddi_root, mdtype="DDI")
    sip.add_dmdsec(
        md="dataset.json",
        mdtype="OTHER",
        mode="mdref",
        label="dataset.json",
        loctype="OTHER",
        otherloctype="SYSTEM",
    )

    # Add original files
    for file_json in j["latestVersion"]["files"]:
        # TODO how to actually tell what is original file?
        if file_json["dataFile"]["filename"].endswith(".tab"):
            # If tabfile, set up bundle
            bundle = create_bundle(file_json)
            sip.add_child(bundle)
        else:
            f = metsrw.FSEntry(
                path=file_json["dataFile"]["filename"],
                use="original",
                file_uuid=str(uuid.uuid4()),
                checksumtype="MD5",
                checksum=file_json["dataFile"]["md5"],
            )
            sip.add_child(f)

    # Add metadata directory
    md_dir = metsrw.FSEntry(path="metadata", use=None, type="Directory")
    sip.add_child(md_dir)
    # Add dataset.json
    f = metsrw.FSEntry(
        path="metadata/dataset.json", use="metadata", file_uuid=str(uuid.uuid4())
    )
    # Add to metadata dir
    md_dir.add_child(f)

    # Write METS
    metadata_path = md_path
    if metadata_path is None:
        metadata_path = os.path.join(sip_dir, "metadata")
    if not os.path.exists(metadata_path):
        os.makedirs(metadata_path)

    metadata_name = md_name
    if metadata_name is None:
        metadata_name = "METS.xml"
    mets_path = os.path.join(metadata_path, metadata_name)
    mets_f = metsrw.METSDocument()
    mets_f.append_file(sip)
    # print(mets_f.tostring(fully_qualified=True).decode('ascii'))
    mets_f.write(mets_path, pretty_print=True, fully_qualified=True)

    return 0


def main(sip_dir):
    return map_dataverse(sip_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sip_dir", type=str, help="The Dataverse transfer folder to process."
    )
    args = parser.parse_args()
    if args.sip_dir == "None":
        sys.exit(0)
    logger.info("dataverse called with args: %s", vars(args))
    sys.exit(main(**vars(args)))
