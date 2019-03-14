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
# @author Joseph Perry <joseph@artefactual.com>

from lxml import etree
import mailbox
import os
import sys
import traceback
import uuid

import django

django.setup()
from django.db import transaction
from django.utils import six

# dashboard
from main.models import File

# archivematicaCommon
from externals.extractMaildirAttachments import parse
from fileOperations import addFileToTransfer, updateSizeAndChecksum
from archivematicaFunctions import unicodeToStr


class State(object):
    def __init__(self):
        self.error_count = 0
        self.sourceFilePath = None
        self.sourceFileUUID = None


def writeFile(filePath, fileContents):
    try:
        os.makedirs(os.path.dirname(filePath))
    except:
        pass
    FILE = open(filePath, "w")
    FILE.writelines(fileContents)
    FILE.close()


def addFile(
    filePath,
    transferPath,
    transferUUID,
    date,
    eventDetail="",
    fileUUID=uuid.uuid4().__str__(),
):
    taskUUID = uuid.uuid4().__str__()
    filePathRelativeToSIP = filePath.replace(transferPath, "%transferDirectory%", 1)
    addFileToTransfer(
        filePathRelativeToSIP,
        fileUUID,
        transferUUID,
        taskUUID,
        date,
        sourceType="unpacking",
        eventDetail=eventDetail,
    )
    updateSizeAndChecksum(fileUUID, filePath, date, uuid.uuid4.__str__())


def getFileUUIDofSourceFile(transferUUID, sourceFilePath):
    try:
        return File.objects.get(
            removedtime__isnull=True,
            transfer_id=transferUUID,
            currentlocation__startswith=sourceFilePath,
        ).uuid
    except File.DoesNotExist:
        return ""


def addKeyFileToNormalizeMaildirOffOf(
    relativePathToRepresent,
    mirrorDir,
    transferPath,
    transferUUID,
    date,
    eventDetail="",
    fileUUID=uuid.uuid4().__str__(),
):
    basename = os.path.basename(mirrorDir)
    dirname = os.path.dirname(mirrorDir)
    outFile = os.path.join(dirname, basename + ".archivematicaMaildir")
    content = """#This file is used in the archivematica system to represent a maildir dirctory, for normalization and permission purposes.
[archivematicaMaildir]
path = %s
    """ % (
        relativePathToRepresent
    )
    f = open(outFile, "w")
    f.write(content)
    f.close()
    addFile(
        outFile,
        transferPath,
        transferUUID,
        date,
        eventDetail=eventDetail,
        fileUUID=fileUUID,
    )
    return


def handle_job(job):
    # http://www.doughellmann.com/PyMOTW/mailbox/
    state = State()
    transferDir = job.args[1]
    transferUUID = job.args[2]
    date = job.args[3]
    maildir = os.path.join(transferDir, "objects", "Maildir")
    outXML = os.path.join(transferDir, "logs", "attachmentExtraction.xml")
    mirrorDir = os.path.join(transferDir, "objects", "attachments")
    try:
        os.makedirs(mirrorDir)
    except os.error:
        pass
    # print "Extracting attachments from: " + maildir
    root = etree.Element("ArchivematicaMaildirAttachmentExtractionRecord")
    root.set("directory", maildir)
    for maildirsub in (
        d for d in os.listdir(maildir) if os.path.isdir(os.path.join(maildir, d))
    ):
        maildirsub_full_path = os.path.join(maildir, maildirsub)
        job.pyprint("Extracting attachments from: " + maildirsub_full_path)
        md = mailbox.Maildir(maildirsub_full_path, None)
        directory = etree.SubElement(root, "subDir")
        directory.set("dir", maildirsub)
        try:
            for item in md.keys():
                try:
                    subDir = md.get_message(item).get_subdir()
                    sourceFilePath2 = os.path.join(maildir, maildirsub, subDir, item)
                    sourceFilePath = sourceFilePath2.replace(
                        transferDir, "%transferDirectory%", 1
                    )
                    sourceFileUUID = getFileUUIDofSourceFile(
                        transferUUID, sourceFilePath
                    )
                    state.sourceFileUUID = sourceFileUUID
                    state.sourceFilePath = sourceFilePath
                    fil = md.get_file(item)
                    out = parse(fil, state)
                    job.pyprint("Email Subject:", out.get("subject"))
                    if out["attachments"]:
                        msg = etree.SubElement(directory, "msg")
                        etree.SubElement(msg, "Message-ID").text = out["msgobj"][
                            "Message-ID"
                        ][1:-1]
                        etree.SubElement(msg, "Extracted-from").text = item
                        if isinstance(out["subject"], six.binary_type):
                            etree.SubElement(msg, "Subject").text = out[
                                "subject"
                            ].decode("utf-8")
                        else:
                            etree.SubElement(msg, "Subject").text = out["subject"]
                        etree.SubElement(msg, "Date").text = out["msgobj"]["date"]
                        etree.SubElement(msg, "To").text = out["to"]
                        etree.SubElement(msg, "From").text = out["from"]
                        for attachment in out["attachments"]:
                            job.pyprint("\tAttachment name:", attachment.name)
                            try:
                                if attachment.name is None:
                                    continue
                                # these are versions of the body of the email - I think
                                if attachment.name == "rtf-body.rtf":
                                    continue
                                attachedFileUUID = uuid.uuid4().__str__()
                                # attachment = StringIO(file_data) TODO LOG TO FILE
                                attch = etree.SubElement(msg, "attachment")
                                etree.SubElement(attch, "name").text = attachment.name
                                etree.SubElement(
                                    attch, "content_type"
                                ).text = attachment.content_type
                                etree.SubElement(attch, "size").text = str(
                                    attachment.size
                                )
                                # print attachment.create_date
                                # FIXME Dates don't appear to be working. Disabling for the moment
                                # etree.SubElement(attch, "create_date").text = attachment.create_date
                                # etree.SubElement(attch, "mod_date").text = attachment.mod_date
                                # etree.SubElement(attch, "read_date").text = attachment.read_date
                                filePath = os.path.join(
                                    transferDir,
                                    "objects",
                                    "attachments",
                                    maildirsub,
                                    subDir,
                                    "%s_%s" % (attachedFileUUID, attachment.name),
                                )
                                job.pyprint("\tAttachment path:", filePath)
                                filePath = unicodeToStr(filePath)
                                writeFile(filePath, attachment)
                                eventDetail = "Unpacked from: {%s}%s" % (
                                    sourceFileUUID,
                                    sourceFilePath,
                                )
                                addFile(
                                    filePath,
                                    transferDir,
                                    transferUUID,
                                    date,
                                    eventDetail=eventDetail,
                                    fileUUID=attachedFileUUID,
                                )
                            except Exception as inst:
                                job.pyprint(sourceFilePath, file=sys.stderr)
                                job.print_error(traceback.format_exc())
                                job.pyprint(
                                    type(inst), file=sys.stderr
                                )  # the exception instance
                                job.pyprint(inst.args, file=sys.stderr)
                                job.pyprint(etree.tostring(msg), file=sys.stderr)
                                job.pyprint(file=sys.stderr)
                                state.error_count += 1
                except Exception as inst:
                    job.pyprint(sourceFilePath, file=sys.stderr)
                    job.print_error(traceback.format_exc())
                    job.pyprint(type(inst), file=sys.stderr)  # the exception instance
                    job.pyprint(inst.args, file=sys.stderr)
                    job.pyprint(file=sys.stderr)
                    state.error_count += 1
        except Exception as inst:
            job.pyprint("INVALID MAILDIR FORMAT", file=sys.stderr)
            job.pyprint(type(inst), file=sys.stderr)
            job.pyprint(inst.args, file=sys.stderr)
            job.set_status(246)  # Was -10, but exit codes are unsigned
            return

        mirrorDir = os.path.join(transferDir, "objects/attachments", maildirsub)
        try:
            os.makedirs(mirrorDir)
        except:
            pass
        eventDetail = "added for normalization purposes"
        fileUUID = uuid.uuid4().__str__()
        addKeyFileToNormalizeMaildirOffOf(
            os.path.join(maildir, maildirsub).replace(
                transferDir, "%transferDirectory%", 1
            ),
            mirrorDir,
            transferDir,
            transferUUID,
            date,
            eventDetail=eventDetail,
            fileUUID=fileUUID,
        )
    tree = etree.ElementTree(root)
    tree.write(outXML, pretty_print=True, xml_declaration=True)

    job.set_status(state.error_count)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                handle_job(job)
