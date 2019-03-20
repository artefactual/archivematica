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
# @subpackage archivematicaCommon
# @author Joseph Perry <joseph@artefactual.com>

from __future__ import absolute_import, print_function
import csv
import os
import uuid
import sys
import shutil

from databaseFunctions import insertIntoFiles
from executeOrRunSubProcess import executeOrRun
from databaseFunctions import insertIntoEvents
import MySQLdb
from archivematicaFunctions import unicodeToStr, get_setting, get_file_checksum

from main.models import File, Transfer


def updateSizeAndChecksum(
    fileUUID,
    filePath,
    date,
    eventIdentifierUUID,
    fileSize=None,
    checksum=None,
    checksumType=None,
    add_event=True,
):
    """
    Update a File with its size, checksum and checksum type. These are
    parameters that can be either generated or provided via keywords.

    Finally, insert the corresponding Event. This behavior can be cancelled
    using the boolean keyword 'add_event'.
    """
    if not fileSize:
        fileSize = os.path.getsize(filePath)
    if not checksumType:
        checksumType = get_setting("checksum_type", "sha256")
    if not checksum:
        checksum = get_file_checksum(filePath, checksumType)

    File.objects.filter(uuid=fileUUID).update(
        size=fileSize, checksum=checksum, checksumtype=checksumType
    )

    if add_event:
        insertIntoEvents(
            fileUUID=fileUUID,
            eventType="message digest calculation",
            eventDateTime=date,
            eventDetail='program="python"; module="hashlib.{}()"'.format(checksumType),
            eventOutcomeDetailNote=checksum,
        )


def addFileToTransfer(
    filePathRelativeToSIP,
    fileUUID,
    transferUUID,
    taskUUID,
    date,
    sourceType="ingestion",
    eventDetail="",
    use="original",
    originalLocation=None,
):
    if not originalLocation:
        originalLocation = filePathRelativeToSIP
    file_obj = insertIntoFiles(
        fileUUID,
        filePathRelativeToSIP,
        date,
        transferUUID=transferUUID,
        use=use,
        originalLocation=originalLocation,
    )
    insertIntoEvents(
        fileUUID=fileUUID,
        eventType=sourceType,
        eventDateTime=date,
        eventDetail=eventDetail,
        eventOutcome="",
        eventOutcomeDetailNote="",
    )
    addAccessionEvent(fileUUID, transferUUID, date)
    return file_obj


def addAccessionEvent(fileUUID, transferUUID, date):
    transfer = Transfer.objects.get(uuid=transferUUID)
    if transfer.accessionid:
        eventOutcomeDetailNote = "accession#" + MySQLdb.escape_string(
            transfer.accessionid
        )
        insertIntoEvents(
            fileUUID=fileUUID,
            eventType="registration",
            eventDateTime=date,
            eventDetail="",
            eventOutcome="",
            eventOutcomeDetailNote=eventOutcomeDetailNote,
        )


def addFileToSIP(
    filePathRelativeToSIP,
    fileUUID,
    sipUUID,
    taskUUID,
    date,
    sourceType="ingestion",
    use="original",
):
    insertIntoFiles(fileUUID, filePathRelativeToSIP, date, sipUUID=sipUUID, use=use)
    insertIntoEvents(
        fileUUID=fileUUID,
        eventType=sourceType,
        eventDateTime=date,
        eventDetail="",
        eventOutcome="",
        eventOutcomeDetailNote="",
    )


def rename(source, destination, printfn=print, should_exit=False):
    """Used to move/rename directories. This function was before used to wrap the operation with sudo."""
    command = ["mv", source, destination]
    exitCode, stdOut, stdError = executeOrRun("command", command, "", printing=False)
    if exitCode:
        printfn("exitCode:", exitCode, file=sys.stderr)
        printfn(stdOut, file=sys.stderr)
        printfn(stdError, file=sys.stderr)
        if should_exit:
            exit(exitCode)


def updateDirectoryLocation(
    src, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith
):
    srcDB = src.replace(unitPath, unitPathReplaceWith)
    if not srcDB.endswith("/") and srcDB != unitPathReplaceWith:
        srcDB += "/"
    dstDB = dst.replace(unitPath, unitPathReplaceWith)
    if not dstDB.endswith("/") and dstDB != unitPathReplaceWith:
        dstDB += "/"

    kwargs = {
        "removedtime__isnull": True,
        "currentlocation__startswith": srcDB,
        unitIdentifierType: unitIdentifier,
    }
    files = File.objects.filter(**kwargs)

    for f in files:
        f.currentlocation = f.currentlocation.replace(srcDB, dstDB)
        f.save()
    if os.path.isdir(dst):
        if dst.endswith("/"):
            dst += "."
        else:
            dst += "/."
    print("moving: ", src, dst)
    shutil.move(src, dst)


class UpdateFileLocationFailed(Exception):
    def __init__(self, code):
        self.code = code


def updateFileLocation2(
    src,
    dst,
    unitPath,
    unitIdentifier,
    unitIdentifierType,
    unitPathReplaceWith,
    printfn=print,
):
    """Dest needs to be the actual full destination path with filename."""
    srcDB = src.replace(unitPath, unitPathReplaceWith)
    dstDB = dst.replace(unitPath, unitPathReplaceWith)
    # Fetch the file UUID
    kwargs = {
        "removedtime__isnull": True,
        "currentlocation": srcDB,
        unitIdentifierType: unitIdentifier,
    }

    try:
        f = File.objects.get(**kwargs)
    except (File.DoesNotExist, File.MultipleObjectsReturned) as e:
        if isinstance(e, File.DoesNotExist):
            message = "no results found"
        else:
            message = "multiple results found"
        printfn(
            "ERROR: file information not found:",
            message,
            "for arguments:",
            repr(kwargs),
            file=sys.stderr,
        )
        raise UpdateFileLocationFailed(4)

    # Move the file
    printfn("Moving", src, "to", dst)
    shutil.move(src, dst)
    # Update the DB
    f.currentlocation = dstDB
    f.save()


def updateFileLocation(
    src,
    dst,
    eventType="",
    eventDateTime="",
    eventDetail="",
    eventIdentifierUUID=uuid.uuid4().__str__(),
    fileUUID="None",
    sipUUID=None,
    transferUUID=None,
    eventOutcomeDetailNote="",
    createEvent=True,
):
    """
    Updates file location in the database, and optionally writes an event for the sanitization to the database.
    Note that this does not actually move a file on disk.
    If the file uuid is not provided, will use the SIP uuid and the old path to find the file uuid.
    To suppress creation of an event, pass the createEvent keyword argument (for example, if the file moved due to the renaming of a parent directory and not the file itself).
    """

    src = unicodeToStr(src)
    dst = unicodeToStr(dst)
    fileUUID = unicodeToStr(fileUUID)
    if not fileUUID or fileUUID == "None":
        kwargs = {"removedtime__isnull": True, "currentlocation": src}

        if sipUUID:
            kwargs["sip_id"] = sipUUID
        elif transferUUID:
            kwargs["transfer_id"] = transferUUID
        else:
            raise ValueError(
                "One of fileUUID, sipUUID, or transferUUID must be provided"
            )

        f = File.objects.get(**kwargs)
    else:
        f = File.objects.get(uuid=fileUUID)

    # UPDATE THE CURRENT FILE PATH
    f.currentlocation = dst
    f.save()

    if not createEvent:
        return

    if eventOutcomeDetailNote == "":
        eventOutcomeDetailNote = 'Original name="%s"; cleaned up name="%s"' % (src, dst)
    # CREATE THE EVENT
    insertIntoEvents(
        fileUUID=f.uuid,
        eventType=eventType,
        eventDateTime=eventDateTime,
        eventDetail=eventDetail,
        eventOutcome="",
        eventOutcomeDetailNote=eventOutcomeDetailNote,
    )


def getFileUUIDLike(
    filePath, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith
):
    """Dest needs to be the actual full destination path with filename."""
    srcDB = filePath.replace(unitPath, unitPathReplaceWith)
    kwargs = {
        "removedtime__isnull": True,
        "currentlocation__contains": srcDB,
        unitIdentifierType: unitIdentifier,
    }
    return {f.currentlocation: f.uuid for f in File.objects.filter(**kwargs)}


def updateFileGrpUsefileGrpUUID(fileUUID, fileGrpUse, fileGrpUUID):
    File.objects.filter(uuid=fileUUID).update(
        filegrpuse=fileGrpUse, filegrpuuid=fileGrpUUID
    )


def updateFileGrpUse(fileUUID, fileGrpUse):
    File.objects.filter(uuid=fileUUID).update(filegrpuse=fileGrpUse)


class FindFileInNormalizatonCSVError(Exception):
    def __init__(self, code):
        self.code = code


def findFileInNormalizationCSV(
    csv_path, commandClassification, target_file, sip_uuid, printfn=print
):
    """ Returns the original filename or None for a manually normalized file.

    :param str csv_path: absolute path to normalization.csv
    :param str commandClassification: "access" or "preservation"
    :param str target_file: Path for access or preservation file to match against, relative to the objects directory
    :param str sip_uuid: UUID of the SIP the files belong to

    :returns: Path to the origin file for `target_file`. Note this is the path from normalization.csv, so will be the original location.
    """
    # use universal newline mode to support unusual newlines, like \r
    with open(csv_path, "rbU") as csv_file:
        reader = csv.reader(csv_file)
        # Search CSV for an access/preservation filename that matches target_file
        # Get original name of target file, to handle sanitized names
        try:
            f = File.objects.get(
                removedtime__isnull=True,
                currentlocation__endswith=target_file,
                sip_id=sip_uuid,
            )
        except File.MultipleObjectsReturned:
            printfn(
                "More than one result found for {} file ({}) in DB.".format(
                    commandClassification, target_file
                ),
                file=sys.stderr,
            )
            raise FindFileInNormalizatonCSVError(2)
        except File.DoesNotExist:
            printfn(
                "{} file ({}) not found in DB.".format(
                    commandClassification, target_file
                ),
                file=sys.stderr,
            )
            raise FindFileInNormalizatonCSVError(2)
        target_file = f.originallocation.replace(
            "%transferDirectory%objects/", "", 1
        ).replace("%SIPDirectory%objects/", "", 1)
        try:
            for row in reader:
                if not row:
                    continue
                if "#" in row[0]:  # ignore comments
                    continue
                original, access, preservation = row
                if commandClassification == "access" and access == target_file:
                    printfn(
                        "Found access file ({0}) for original ({1})".format(
                            access, original
                        )
                    )
                    return original
                if (
                    commandClassification == "preservation"
                    and preservation == target_file
                ):
                    printfn(
                        "Found preservation file ({0}) for original ({1})".format(
                            preservation, original
                        )
                    )
                    return original
            else:
                return None
        except csv.Error:
            printfn(
                "Error reading {filename} on line {linenum}".format(
                    filename=csv_path, linenum=reader.line_num
                ),
                file=sys.stderr,
            )
            raise FindFileInNormalizatonCSVError(2)
