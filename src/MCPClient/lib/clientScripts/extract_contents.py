#!/usr/bin/env python2

import os
import sys
import uuid

import django
from django.db import transaction
django.setup()
# dashboard
from fpr.models import FPCommand
from main.models import Directory, FileFormatVersion, File, Transfer

# archivematicaCommon
from custom_handlers import get_script_logger
from executeOrRunSubProcess import executeOrRun
from databaseFunctions import fileWasRemoved
from fileOperations import (
    addFileToTransfer,
    updateSizeAndChecksum,
    rename,
    updateFileLocation,
)
from archivematicaFunctions import get_dir_uuids, format_subdir_path

# clientScripts
from has_packages import already_extracted, AM_DATE_DELIMITER

file_path_cache = {}

logger = get_script_logger("archivematica.mcp.client.extractContents")

TRANSFER_DIRECTORY = "%transferDirectory%"


def suffix_date(file_path, date):
    return file_path + AM_DATE_DELIMITER + date


def tree(root):
    for dirpath, __, files in os.walk(root):
        for file in files:
            yield os.path.join(dirpath, file)


def assign_uuid(job, filename, package_uuid, transfer_uuid, date, task_uuid,
                sip_directory, package_filename, original_location,
                sanitized_original_location):
    """Assign a uuid to each file in the extracted package."""
    file_uuid = uuid.uuid4().__str__()
    location_to_replace = format_subdir_path(sanitized_original_location,
                                             sip_directory)
    # Correct the information in the path strings sent to this function. First
    # remove the SIP directory from the string. Second, make sure that file
    # paths have not been modified for processing purpose, i.e. in
    # Archivematica current terminology, sanitized.
    relative_path = filename.replace(sip_directory, TRANSFER_DIRECTORY, 1)
    transfer_path = relative_path.replace(location_to_replace,
                                          os.path.join(original_location, ''))
    relative_package_path = package_filename.replace(sip_directory,
                                                     TRANSFER_DIRECTORY, 1)
    package_detail = "{} ({})".format(relative_package_path, package_uuid)
    event_detail = "Unpacked from: " + package_detail
    addFileToTransfer(relative_path, file_uuid, transfer_uuid, task_uuid, date,
                      sourceType="unpacking", eventDetail=event_detail,
                      originalLocation=transfer_path)
    updateSizeAndChecksum(file_uuid, filename, date, uuid.uuid4().__str__())
    job.pyprint('Assigning new file UUID:', file_uuid, 'to file', filename)


def _get_subdir_paths(job, root_path,
                      path_prefix_to_repl,
                      original_location):
    """Return a generator of subdirectory paths in ``root_path`` with
    the ancestor path ``path_prefix_to_repl`` replaced by a placeholder
    string. ``original_location`` should be the zip container that the content
    was extracted from as it was transferred. Between then and now the path
    will have been changed to remove characters that are difficult for tools
    to handle. PREMIS describes the original location as how it was received
    not what it was changed to, so we make these changes below to reflect the
    original transfer material.
    """
    # Make sure that the original location is suffixed with a trailing slash
    # as it is a directory.
    original_location = os.path.join(original_location, '')
    # Transform the processing directory string to reflect where it was when
    # transferred, that is, in the ``%transferDirectory%``.
    location_to_replace = format_subdir_path(root_path,
                                             path_prefix_to_repl)

    # Return a generator here that contains information about the current path
    # and the original path for the PREMIS information in the METS file.
    for dir_path, __, ___ in os.walk(root_path):
        formatted_path = format_subdir_path(dir_path, path_prefix_to_repl)
        for dir_uuid in get_dir_uuids(
                [formatted_path], logger, printfn=job.pyprint):
            dir_uuid["originalLocation"] = formatted_path\
                .replace(location_to_replace, original_location)
            yield dir_uuid


def delete_and_record_package_file(job, file_path, file_uuid, current_location):
    os.remove(file_path)
    job.pyprint("Package removed: " + file_path)
    event_detail_note = "removed from: " + current_location
    fileWasRemoved(file_uuid, eventDetail=event_detail_note)


def main(job, transfer_uuid, sip_directory, date, task_uuid, delete=False):
    files = File.objects.filter(transfer=transfer_uuid,
                                removedtime__isnull=True)
    if not files:
        job.pyprint('No files found for transfer: ', transfer_uuid)

    transfer_mdl = Transfer.objects.get(uuid=transfer_uuid)

    # We track whether or not anything was extracted because that controls what
    # the next microservice chain link will be.
    # If something was extracted, then a new identification step has to be
    # kicked off on those files; otherwise, we can go ahead with the transfer.
    extracted = False

    for file_ in files:
        try:
            format_id = FileFormatVersion.objects.get(file_uuid=file_.uuid)
        # Can't do anything if the file wasn't identified in the previous step
        except:
            job.pyprint('Not extracting contents from',
                        os.path.basename(file_.currentlocation),
                        ' - file format not identified',
                        file=sys.stderr)
            continue
        if format_id.format_version is None:
            job.pyprint('Not extracting contents from',
                        os.path.basename(file_.currentlocation),
                        ' - file format not identified',
                        file=sys.stderr)
            continue
        # Extraction commands are defined in the FPR just like normalization
        # commands
        try:
            command = FPCommand.active.get(
                fprule__format=format_id.format_version,
                fprule__purpose='extract',
                fprule__enabled=True,
            )
        except FPCommand.DoesNotExist:
            job.pyprint('Not extracting contents from',
                        os.path.basename(file_.currentlocation),
                        ' - No rule found to extract',
                        file=sys.stderr)
            continue

        # Check if file has already been extracted
        if already_extracted(file_):
            job.pyprint('Not extracting contents from',
                        os.path.basename(file_.currentlocation),
                        ' - extraction already happened.',
                        file=sys.stderr)
            continue

        output_file_path = file_.currentlocation.replace(TRANSFER_DIRECTORY,
                                                         sip_directory)

        # Rename the input package so that when we extract the
        # contents we don't extract it to a directory that will conflict with
        # the names we want to preserve in our PREMIS:originalLocation.
        new_package_realpath = suffix_date(output_file_path, date)
        rename(output_file_path, new_package_realpath)

        # Create the extract packages command.
        if command.script_type == 'command' or command.script_type == 'bashScript':
            args = []
            command_to_execute = command.command.replace('%inputFile%',
                                                         new_package_realpath)
            command_to_execute = command_to_execute.replace('%outputDirectory%',
                                                            output_file_path)
        else:
            command_to_execute = command.command
            args = [new_package_realpath, output_file_path]

        # Make the command clear to users when inspecting stdin/stdout.
        logger.info("Command to execute is: %s", command_to_execute)
        exitstatus, stdout, stderr = executeOrRun(command.script_type,
                                                  command_to_execute,
                                                  arguments=args,
                                                  printing=True,
                                                  capture_output=True)
        job.write_output(stdout)
        job.write_error(stderr)

        if not exitstatus == 0:
            # Dang, looks like the extraction failed
            job.pyprint('Command', command.description, 'failed!',
                        file=sys.stderr)
        else:
            extracted = True
            job.pyprint('Extracted contents from',
                        os.path.basename(output_file_path))

            # Assign UUIDs and insert them into the database, so the newly-
            # extracted files are properly tracked by Archivematica
            for extracted_file in tree(output_file_path):
                assign_uuid(
                    job, extracted_file, file_.uuid, transfer_uuid, date,
                    task_uuid, sip_directory, file_.currentlocation,
                    file_.originallocation, output_file_path)

            if transfer_mdl.diruuids:
                create_extracted_dir_uuids(
                    job, transfer_mdl, output_file_path, sip_directory, file_)

            if delete:
                # Remove the original package file after extracting its contents
                delete_and_record_package_file(
                    job, new_package_realpath, file_.uuid, file_.currentlocation)
            else:
                # Or document the moving of the package file.
                old_currentlocation = file_.currentlocation
                new_currentlocation = suffix_date(old_currentlocation, date)
                event_outcome_detail_note = (
                    'moved from="{}"; moved to="{}"'.format(
                        old_currentlocation, new_currentlocation))
                updateFileLocation(
                    old_currentlocation,
                    new_currentlocation,
                    eventType='movement',
                    eventDateTime=date,
                    eventDetail='',
                    fileUUID=file_.uuid,
                    transferUUID=transfer_uuid,
                    eventOutcomeDetailNote=event_outcome_detail_note)

    if extracted:
        return 0
    else:
        return 255


def create_extracted_dir_uuids(
        job, transfer_mdl, output_file_path, sip_directory, file_):
    """Assign UUIDs to directories via ``Directory`` objects in the database.
    """
    Directory.create_many(
        _get_subdir_paths(
            job,
            output_file_path,
            sip_directory,
            file_.originallocation),
        transfer_mdl)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                transfer_uuid = job.args[1]
                sip_directory = job.args[2]
                date = job.args[3]
                task_uuid = job.args[4]
                # Whether or not to remove the package file post-extraction
                # This is set by the user during the transfer, and defaults to false.
                delete = False
                if job.args[5] == "True":
                    delete = True
                job.pyprint("Deleting?: {}".format(delete), file=sys.stderr)
                job.set_status(main(job, transfer_uuid, sip_directory, date, task_uuid, delete=delete))
