# -*- coding: utf-8 -*-

import os
import sys
import lxml.etree as etree

# dashboard
from main.models import File

# archivematicaCommon
import namespaces as ns


def createMDRefDMDSec(LABEL, itemdirectoryPath, directoryPathSTR):
    XPTR = "xpointer(id("
    tree = etree.parse(itemdirectoryPath)
    root = tree.getroot()
    # a = """<amdSec ID="amd_496"><rightsMD ID="rightsMD_499">"""
    for item in root.findall(
        "{http://www.loc.gov/METS/}amdSec/{http://www.loc.gov/METS/}rightsMD"
    ):
        # print "rights id:", item.get("ID")
        XPTR = "%s %s" % (XPTR, item.get("ID"))
    XPTR = XPTR.replace(" ", "'", 1) + "'))"
    mdRef = etree.Element(ns.metsBNS + "mdRef")
    mdRef.set("LABEL", LABEL)
    mdRef.set(ns.xlinkBNS + "href", directoryPathSTR)
    mdRef.set("MDTYPE", "OTHER")
    mdRef.set("OTHERMDTYPE", "METSRIGHTS")
    mdRef.set("LOCTYPE", "OTHER")
    mdRef.set("OTHERLOCTYPE", "SYSTEM")
    mdRef.set("XPTR", XPTR)
    return mdRef


def archivematicaCreateMETSRightsDspaceMDRef(
    job, fileUUID, filePath, transferUUID, itemdirectoryPath, state
):
    ret = []
    try:
        job.pyprint(fileUUID, filePath)
        # Find the mets file. May find none.
        path = "%SIPDirectory%{}/mets.xml".format(os.path.dirname(filePath))
        try:
            mets = File.objects.get(currentlocation=path, transfer_id=transferUUID)
        except File.DoesNotExist:
            pass
        else:
            metsFileUUID = mets.uuid
            metsLoc = mets.currentlocation.replace("%SIPDirectory%", "", 1)
            metsLocation = os.path.join(os.path.dirname(itemdirectoryPath), "mets.xml")
            LABEL = "mets.xml-%s" % (metsFileUUID)
            ret.append(createMDRefDMDSec(LABEL, metsLocation, metsLoc))

        base = os.path.dirname(os.path.dirname(itemdirectoryPath))
        base2 = os.path.dirname(os.path.dirname(filePath))

        for dir_ in os.listdir(base):
            fullDir = os.path.join(base, dir_)
            fullDir2 = os.path.join(base2, dir_)
            job.pyprint(fullDir)
            if dir_.startswith("ITEM"):
                job.pyprint("continue")
                continue
            if not os.path.isdir(fullDir):
                continue

            path = "%SIPDirectory%{}/mets.xml".format(fullDir2)
            try:
                f = File.objects.get(currentlocation=path, transfer_id=transferUUID)
            except File.DoesNotExist:
                pass
            else:
                metsFileUUID = f.uuid
                metsLoc = f.currentlocation.replace("%SIPDirectory%", "", 1)
                metsLocation = os.path.join(fullDir, "mets.xml")
                job.pyprint(metsLocation)
                LABEL = "mets.xml-" + metsFileUUID
                ret.append(createMDRefDMDSec(LABEL, metsLocation, metsLoc))

    except Exception as inst:
        job.pyprint(
            "Error creating mets dspace mdref", fileUUID, filePath, file=sys.stderr
        )
        job.pyprint(type(inst), inst.args, file=sys.stderr)
        state.error_accumulator.error_count += 1

    return ret
