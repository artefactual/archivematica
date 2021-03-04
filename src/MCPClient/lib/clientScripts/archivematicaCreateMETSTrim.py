#!/usr/bin/env python2
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import os
import sys
import lxml.etree as etree

# dashboard
from main.models import File

import namespaces as ns


def getTrimDmdSec(job, baseDirectoryPath, fileGroupIdentifier):
    # containerMetadata
    ret = etree.Element(ns.metsBNS + "dmdSec")
    mdWrap = etree.SubElement(ret, ns.metsBNS + "mdWrap")
    mdWrap.set("MDTYPE", "DC")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")

    dublincore = etree.SubElement(
        xmlData, ns.dctermsBNS + "dublincore", attrib=None, nsmap={"dc": ns.dctermsNS}
    )
    dublincore.set(
        ns.xsiBNS + "schemaLocation",
        ns.dctermsNS + " http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd",
    )
    tree = etree.parse(
        os.path.join(baseDirectoryPath, "objects", "ContainerMetadata.xml")
    )
    root = tree.getroot()

    etree.SubElement(dublincore, ns.dctermsBNS + "title").text = root.find(
        "Container/TitleFreeTextPart"
    ).text
    etree.SubElement(
        dublincore, ns.dctermsBNS + "provenance"
    ).text = "Department: %s; OPR: %s" % (
        root.find("Container/Department").text,
        root.find("Container/OPR").text,
    )
    etree.SubElement(dublincore, ns.dctermsBNS + "isPartOf").text = root.find(
        "Container/FullClassificationNumber"
    ).text
    etree.SubElement(dublincore, ns.dctermsBNS + "identifier").text = root.find(
        "Container/RecordNumber"
    ).text.split("/")[-1]

    # get objects count
    files = File.objects.filter(
        removedtime__isnull=True, sip_id=fileGroupIdentifier, filegrpuse="original"
    )
    etree.SubElement(
        dublincore, ns.dctermsBNS + "extent"
    ).text = "{} digital objects".format(files.count())

    files = File.objects.filter(
        removedtime__isnull=True,
        sip_id=fileGroupIdentifier,
        filegrpuse="TRIM file metadata",
    )

    minDateMod = None
    maxDateMod = None
    for f in files:
        fileMetadataXmlPath = f.currentlocation.replace(
            "%SIPDirectory%", baseDirectoryPath, 1
        )
        if os.path.isfile(fileMetadataXmlPath):
            tree2 = etree.parse(fileMetadataXmlPath)
            root2 = tree2.getroot()
            dateMod = root2.find("Document/DateModified").text
            if minDateMod is None or dateMod < minDateMod:
                minDateMod = dateMod
            if maxDateMod is None or dateMod > maxDateMod:
                maxDateMod = dateMod

    etree.SubElement(dublincore, ns.dctermsBNS + "date").text = "%s/%s" % (
        minDateMod,
        maxDateMod,
    )

    # print etree.tostring(dublincore, pretty_print = True)
    return ret


def getTrimFileDmdSec(job, baseDirectoryPath, fileGroupIdentifier, fileUUID):
    ret = etree.Element(ns.metsBNS + "dmdSec")
    mdWrap = etree.SubElement(ret, ns.metsBNS + "mdWrap")
    mdWrap.set("MDTYPE", "DC")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")

    try:
        f = File.objects.get(
            removedtime__isnull=True,
            sip_id=fileGroupIdentifier,
            filegrpuuid=fileUUID,
            filegrpuse="TRIM file metadata",
        )
    except File.DoesNotExist:
        job.pyprint("no metadata for original file: ", fileUUID, file=sys.stderr)
        return None
    else:
        xmlFilePath = f.currentlocation.replace("%SIPDirectory%", baseDirectoryPath, 1)
        dublincore = etree.SubElement(
            xmlData,
            ns.dctermsBNS + "dublincore",
            attrib=None,
            nsmap={"dc": ns.dctermsNS},
        )
        tree = etree.parse(os.path.join(baseDirectoryPath, xmlFilePath))
        root = tree.getroot()

        etree.SubElement(dublincore, ns.dctermsBNS + "title").text = root.find(
            "Document/TitleFreeTextPart"
        ).text
        etree.SubElement(dublincore, ns.dctermsBNS + "date").text = root.find(
            "Document/DateModified"
        ).text
        etree.SubElement(dublincore, ns.dctermsBNS + "identifier").text = root.find(
            "Document/RecordNumber"
        ).text

    return ret


def getTrimFileAmdSec(job, baseDirectoryPath, fileGroupIdentifier, fileUUID):
    ret = etree.Element(ns.metsBNS + "digiprovMD")

    try:
        f = File.objects.get(
            removedtime__isnull=True,
            sip_id=fileGroupIdentifier,
            filegrpuuid=fileUUID,
            filegrpuse="TRIM file metadata",
        )
    except File.DoesNotExist:
        job.pyprint("no metadata for original file: ", fileUUID, file=sys.stderr)
        return None
    else:
        label = os.path.basename(f.currentlocation)
        attrib = {
            "LABEL": label,
            ns.xlinkBNS + "href": f.currentlocation.replace("%SIPDirectory%", "", 1),
            "MDTYPE": "OTHER",
            "OTHERMDTYPE": "CUSTOM",
            "LOCTYPE": "OTHER",
            "OTHERLOCTYPE": "SYSTEM",
        }
        etree.SubElement(ret, ns.metsBNS + "mdRef", attrib=attrib)
    return ret


def getTrimAmdSec(job, baseDirectoryPath, fileGroupIdentifier):
    ret = etree.Element(ns.metsBNS + "digiprovMD")

    files = File.objects.filter(
        removedtime__isnull=True,
        sip_id=fileGroupIdentifier,
        filegrpuse="TRIM container metadata",
    )
    for f in files:
        attrib = {
            "LABEL": "ContainerMetadata.xml",
            ns.xlinkBNS + "href": f.currentlocation.replace("%SIPDirectory%", "", 1),
            "MDTYPE": "OTHER",
            "OTHERMDTYPE": "CUSTOM",
            "LOCTYPE": "OTHER",
            "OTHERLOCTYPE": "SYSTEM",
        }
        etree.SubElement(ret, ns.metsBNS + "mdRef", attrib=attrib)
    return ret
