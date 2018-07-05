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
from fileOperations import addFileToTransfer, updateSizeAndChecksum
from archivematicaFunctions import get_dir_uuids, format_subdir_path

# clientScripts
from hasPackages import already_extracted

file_path_cache = {}


logger = get_script_logger("archivematica.mcp.client.extractContents")


def output_directory(file_path, date):
    if file_path_cache.get(file_path):
        return file_path_cache[file_path]
    else:
        path = file_path + '-' + date
        file_path_cache[file_path] = path
        return path


def tree(root):
    for dirpath, __, files in os.walk(root):
        for file in files:
            yield os.path.join(dirpath, file)


def assign_uuid(job, filename, package_uuid, transfer_uuid, date, task_uuid, sip_directory, package_filename):
    file_uuid = uuid.uuid4().__str__()
    relative_path = filename.replace(sip_directory, "%transferDirectory%", 1)
    relative_package_path = package_filename.replace(sip_directory, "%transferDirectory%", 1)
    package_detail = "{} ({})".format(relative_package_path, package_uuid)
    event_detail = "Unpacked from: " + package_detail
    addFileToTransfer(relative_path, file_uuid, transfer_uuid, task_uuid, date,
                      sourceType="unpacking", eventDetail=event_detail)
    updateSizeAndChecksum(file_uuid, filename, date, uuid.uuid4().__str__())

    job.pyprint('Assigning new file UUID:', file_uuid, 'to file', filename)


def _get_subdir_paths(root_path, path_prefix_to_repl):
    """Return a generator of subdirectory paths in ``root_path`` with
    the ancestor path ``path_prefix_to_repl`` replaced by a placeholder
    string.
    """
    return (format_subdir_path(dir_path, path_prefix_to_repl) for
            dir_path, __, ___ in os.walk(root_path))


def delete_and_record_package_file(job, file_path, file_uuid, current_location):
    os.remove(file_path)
    job.pyprint("Package removed: " + file_path)
    event_detail_note = "removed from: " + current_location
    fileWasRemoved(file_uuid, eventDetail=event_detail_note)


def main(job, transfer_uuid, sip_directory, date, task_uuid, delete=False):
    files = File.objects.filter(transfer=transfer_uuid, removedtime__isnull=True)
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

        file_path = file_.currentlocation.replace('%transferDirectory%', sip_directory)

        if command.script_type == 'command' or command.script_type == 'bashScript':
            args = []
            command_to_execute = command.command.replace('%inputFile%',
                                                         file_path)
            command_to_execute = command_to_execute.replace('%outputDirectory%',
                                                            output_directory(file_path, date))
        else:
            command_to_execute = command.command
            args = [file_path, output_directory(file_path, date)]

        exitstatus, stdout, stderr = executeOrRun(command.script_type,
                                                  command_to_execute,
                                                  arguments=args,
                                                  printing=True,
                                                  capture_output=True)
        job.write_output(stdout)
        job.write_error(stderr)

        if not exitstatus == 0:
            # Dang, looks like the extraction failed
            job.pyprint('Command', command.description, 'failed!', file=sys.stderr)
        else:
            extracted = True
            job.pyprint('Extracted contents from', os.path.basename(file_path))

            # Assign UUIDs and insert them into the database, so the newly-
            # extracted files are properly tracked by Archivematica
            extracted_path = output_directory(file_path, date)
            for extracted_file in tree(extracted_path):
                assign_uuid(job,
                            extracted_file, file_.uuid, transfer_uuid, date,
                            task_uuid, sip_directory, file_.currentlocation)

            # Assign UUIDs to directories via ``Directory`` objects in the
            # database.
            if transfer_mdl.diruuids:
                Directory.create_many(
                    get_dir_uuids(
                        _get_subdir_paths(extracted_path, sip_directory),
                        logger,
                        printfn=job.pyprint),
                    transfer_mdl)

            # We may want to remove the original package file after extracting its contents
            if delete:
                delete_and_record_package_file(job, file_path, file_.uuid, file_.currentlocation)

    if extracted:
        return 0
    else:
        return 255


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
