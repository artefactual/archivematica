#!/usr/bin/env python2

import argparse
import csv
import errno
import os
import shutil
import traceback
import uuid

from django.utils import timezone

from . import transcoder

import django
import scandir

django.setup()
# dashboard
from fpr.models import FPRule
from main.models import Derivation, FileFormatVersion, File, FileID
from django.db import transaction

# archivematicaCommon
import databaseFunctions
import fileOperations
from dicts import ReplacementDict

from django.conf import settings as mcpclient_settings
from .lib import setup_dicts


# Return codes
SUCCESS = 0
RULE_FAILED = 1
NO_RULE_FOUND = 2


def get_replacement_dict(job, opts):
    """ Generates values for all knows %var% replacement variables. """
    prefix = ""
    postfix = ""
    output_dir = ""
    # get file name and extension
    (directory, basename) = os.path.split(opts.file_path)
    directory += os.path.sep  # All paths should have trailing /
    (filename, extension_dot) = os.path.splitext(basename)

    if "preservation" in opts.purpose:
        postfix = "-" + opts.task_uuid
        output_dir = directory
    elif "access" in opts.purpose:
        prefix = opts.file_uuid + "-"
        output_dir = os.path.join(opts.sip_path, "DIP", "objects") + os.path.sep
    elif "thumbnail" in opts.purpose:
        output_dir = os.path.join(opts.sip_path, "thumbnails") + os.path.sep
        postfix = opts.file_uuid
    else:
        job.print_error("Unsupported command purpose", opts.purpose)
        return None

    # Populates the standard set of unit variables, so,
    # e.g., %fileUUID% is available
    replacement_dict = ReplacementDict.frommodel(type_="file", file_=opts.file_uuid)

    output_filename = "".join([prefix, filename, postfix])
    replacement_dict.update(
        {
            "%outputDirectory%": output_dir,
            "%prefix%": prefix,
            "%postfix%": postfix,
            "%outputFileName%": output_filename,  # does not include extension
            "%outputFilePath%": os.path.join(
                output_dir, output_filename
            ),  # does not include extension
        }
    )
    return replacement_dict


def check_manual_normalization(job, opts):
    """Checks for manually normalized file, returns that path or None.

    Checks by looking for access/preservation files for a give original file.

    Check the manualNormalization/access and manualNormalization/preservation
    directories for access and preservation files.  If a nomalization.csv
    file is specified, check there first for the mapping between original
    file and access/preservation file."""

    # If normalization.csv provided, check there for mapping from original
    # to access/preservation file
    normalization_csv = os.path.join(
        opts.sip_path, "objects", "manualNormalization", "normalization.csv"
    )
    # Get original name of target file, to handle filename changes.
    file_ = File.objects.get(uuid=opts.file_uuid)
    bname = file_.originallocation.replace(
        "%transferDirectory%objects/", "", 1
    ).replace("%SIPDirectory%objects/", "", 1)
    if os.path.isfile(normalization_csv):
        found = False
        # use universal newline mode to support unusual newlines, like \r
        with open(normalization_csv, "rbU") as csv_file:
            reader = csv.reader(csv_file)
            # Search the file for an original filename that matches the one provided
            try:
                for row in reader:
                    if not row:
                        continue
                    if "#" in row[0]:  # ignore comments
                        continue
                    original, access_file, preservation_file = row
                    if original == bname:
                        job.print_output(
                            "Filename",
                            bname,
                            "matches entry in normalization.csv",
                            original,
                        )
                        found = True
                        break
            except csv.Error:
                job.print_error(
                    "Error reading", normalization_csv, " on line", reader.line_num
                )
                job.print_error(traceback.format_exc())
                return None

        # If we didn't find a match, let it fall through to the usual method
        if found:
            # No manually normalized file for command classification
            if "preservation" in opts.purpose and not preservation_file:
                return None
            if "access" in opts.purpose and not access_file:
                return None

            # If we found a match, verify access/preservation exists in DB
            # match and pull original location b/c filename changes
            if "preservation" in opts.purpose:
                filename = preservation_file
            elif "access" in opts.purpose:
                filename = access_file
            else:
                return None
            job.print_output("Looking for", filename, "in database")
            # FIXME: SQL uses removedtime=0. Convince Django to express this
            return File.objects.get(
                sip=opts.sip_uuid, originallocation__iendswith=filename
            )  # removedtime = 0

    # Assume that any access/preservation file found with the right
    # name is the correct one
    # Strip extension, replace SIP path with %var%
    path = os.path.splitext(opts.file_path.replace(opts.sip_path, "%SIPDirectory%", 1))[
        0
    ]
    if "preservation" in opts.purpose:
        path = path.replace(
            "%SIPDirectory%objects/",
            "%SIPDirectory%objects/manualNormalization/preservation/",
        )
    elif "access" in opts.purpose:
        path = path.replace(
            "%SIPDirectory%objects/",
            "%SIPDirectory%objects/manualNormalization/access/",
        )
    else:
        return None

    # FIXME: SQL uses removedtime=0. Cannot get Django to express this
    job.print_output(
        "Checking for a manually normalized file by trying to get the"
        " unique file that matches SIP UUID {} and whose currentlocation"
        " value starts with this path: {}.".format(opts.sip_uuid, path)
    )
    matches = File.objects.filter(  # removedtime = 0
        sip=opts.sip_uuid, currentlocation__startswith=path
    )
    if not matches:
        # No file with the correct path found, assume not manually normalized
        job.print_output("No such file found.")
        return None
    if len(matches) > 1:
        # If multiple matches, the shortest one should be the correct one. E.g.,
        # if original is /a/b/abc.NEF then /a/b/abc.tif and /a/b/abc_1.tif will
        # both match but /a/b/abc.tif is the correct match.
        job.print_output(
            "Multiple files matching path {} found. Returning the shortest one."
        )
        ret = sorted(matches, key=lambda f: f.currentlocation)[0]
        job.print_output("Returning file at {}".format(ret.currentlocation))
        return ret
    return matches[0]


def once_normalized(job, command, opts, replacement_dict):
    """Updates the database if normalization completed successfully.

    Callback from transcoder.Command

    For preservation files, adds a normalization event, and derivation, as well
    as updating the size and checksum for the new file in the DB.  Adds format
    information for use in the METS file to FilesIDs.
    """
    transcoded_files = []
    if not command.output_location:
        command.output_location = ""
    if os.path.isfile(command.output_location):
        transcoded_files.append(command.output_location)
    elif os.path.isdir(command.output_location):
        for w in scandir.walk(command.output_location):
            path, _, files = w
            for p in files:
                p = os.path.join(path, p)
                if os.path.isfile(p):
                    transcoded_files.append(p)
    elif command.output_location:
        job.print_error(
            "Error - output file does not exist [", command.output_location, "]"
        )
        command.exit_code = -2

    derivation_event_uuid = str(uuid.uuid4())
    event_detail_output = 'ArchivematicaFPRCommandID="{}"'.format(
        command.fpcommand.uuid
    )
    if command.event_detail_command is not None:
        event_detail_output += "; {}".format(command.event_detail_command.std_out)
    for ef in transcoded_files:
        if "thumbnails" in opts.purpose:
            continue

        today = timezone.now()
        output_file_uuid = opts.task_uuid  # Match the UUID on disk
        # TODO Add manual normalization for files of same name mapping?
        # Add the new file to the SIP
        path_relative_to_sip = ef.replace(opts.sip_path, "%SIPDirectory%", 1)
        fileOperations.addFileToSIP(
            path_relative_to_sip,
            output_file_uuid,  # File UUID
            opts.sip_uuid,  # SIP UUID
            opts.task_uuid,  # Task UUID
            today,  # Current date
            sourceType="creation",
            use=opts.purpose,
        )

        # Calculate new file checksum
        fileOperations.updateSizeAndChecksum(
            output_file_uuid,  # File UUID, same as task UUID for preservation
            ef,  # File path
            today,  # Date
            str(uuid.uuid4()),  # Event UUID, new UUID
        )

        # Add derivation link and associated event
        #
        # Track both events and insert into Derivations table for
        # preservation copies
        if "preservation" in opts.purpose:
            insert_derivation_event(
                original_uuid=opts.file_uuid,
                output_uuid=output_file_uuid,
                derivation_uuid=derivation_event_uuid,
                event_detail_output=event_detail_output,
                outcome_detail_note=path_relative_to_sip,
                today=today,
            )
        # Other derivatives go into the Derivations table, but
        # don't get added to the PREMIS Events because they will
        # not appear in the METS.
        else:
            d = Derivation(
                source_file_id=opts.file_uuid,
                derived_file_id=output_file_uuid,
                event=None,
            )
            d.save()

        # Use the format info from the normalization command
        # to save identification into the DB
        ffv = FileFormatVersion(
            file_uuid_id=output_file_uuid,
            format_version=command.fpcommand.output_format,
        )
        ffv.save()

        FileID.objects.create(
            file_id=output_file_uuid,
            format_name=command.fpcommand.output_format.format.description,
        )


def once_normalized_callback(job):
    def wrapper(*args):
        return once_normalized(job, *args)

    return wrapper


def insert_derivation_event(
    original_uuid,
    output_uuid,
    derivation_uuid,
    event_detail_output,
    outcome_detail_note,
    today=None,
):
    """ Add the derivation link for preservation files and the event. """
    if today is None:
        today = timezone.now()
    # Add event information to current file
    databaseFunctions.insertIntoEvents(
        fileUUID=original_uuid,
        eventIdentifierUUID=derivation_uuid,
        eventType="normalization",
        eventDateTime=today,
        eventDetail=event_detail_output,
        eventOutcome="",
        eventOutcomeDetailNote=outcome_detail_note or "",
    )

    # Add linking information between files
    databaseFunctions.insertIntoDerivations(
        sourceFileUUID=original_uuid,
        derivedFileUUID=output_uuid,
        relatedEventUUID=derivation_uuid,
    )


def get_default_rule(purpose):
    return FPRule.active.get(purpose="default_" + purpose)


def main(job, opts):
    """ Find and execute normalization commands on input file. """
    # TODO fix for maildir working only on attachments

    setup_dicts(mcpclient_settings)

    # Find the file and it's FormatVersion (file identification)
    try:
        file_ = File.objects.get(uuid=opts.file_uuid)
    except File.DoesNotExist:
        job.print_error("File with uuid", opts.file_uuid, "does not exist in database.")
        return NO_RULE_FOUND
    job.print_output("File found:", file_.uuid, file_.currentlocation)

    # Unless normalization file group use is submissionDocumentation, skip the
    # submissionDocumentation directory
    if (
        opts.normalize_file_grp_use != "submissionDocumentation"
        and file_.currentlocation.startswith(
            "%SIPDirectory%objects/submissionDocumentation"
        )
    ):
        job.print_output(
            "File",
            os.path.basename(opts.file_path),
            "in objects/submissionDocumentation, skipping",
        )
        return SUCCESS

    # Only normalize files where the file's group use and normalize group use match
    if file_.filegrpuse != opts.normalize_file_grp_use:
        job.print_output(
            os.path.basename(opts.file_path),
            "is file group usage",
            file_.filegrpuse,
            "instead of ",
            opts.normalize_file_grp_use,
            " - skipping",
        )
        return SUCCESS

    # For re-ingest: clean up old derivations
    # If the file already has a Derivation with the same purpose, remove it and mark the derived file as deleted
    derivatives = Derivation.objects.filter(
        source_file=file_, derived_file__filegrpuse=opts.purpose
    )
    for derivative in derivatives:
        job.print_output(
            opts.purpose,
            "derivative",
            derivative.derived_file_id,
            "already exists, marking as deleted",
        )
        File.objects.filter(uuid=derivative.derived_file_id).update(
            filegrpuse="deleted"
        )
        # Don't create events for thumbnail files
        if opts.purpose != "thumbnail":
            databaseFunctions.insertIntoEvents(
                fileUUID=derivative.derived_file_id, eventType="deletion"
            )
    derivatives.delete()

    # If a file has been manually normalized for this purpose, skip it
    manually_normalized_file = check_manual_normalization(job, opts)
    if manually_normalized_file:
        job.print_output(
            os.path.basename(opts.file_path),
            "was already manually normalized into",
            manually_normalized_file.currentlocation,
        )
        if "preservation" in opts.purpose:
            # Add derivation link and associated event
            insert_derivation_event(
                original_uuid=opts.file_uuid,
                output_uuid=manually_normalized_file.uuid,
                derivation_uuid=str(uuid.uuid4()),
                event_detail_output="manual normalization",
                outcome_detail_note=None,
            )
        return SUCCESS

    do_fallback = False
    try:
        format_id = FileFormatVersion.objects.get(file_uuid=opts.file_uuid)
    except FileFormatVersion.DoesNotExist:
        format_id = None

    # Look up the normalization command in the FPR
    if format_id:
        job.print_output("File format:", format_id.format_version)
        try:
            rule = FPRule.active.get(
                format=format_id.format_version, purpose=opts.purpose
            )
        except FPRule.DoesNotExist:
            if (
                opts.purpose == "thumbnail"
                and opts.thumbnail_mode == "generate_non_default"
            ):
                job.pyprint("Thumbnail not generated as no rule found for format")
                return SUCCESS
            else:
                do_fallback = True

    # Try with default rule if no format_id or rule was found
    if format_id is None or do_fallback:
        try:
            rule = get_default_rule(opts.purpose)
            job.print_output(
                os.path.basename(file_.currentlocation),
                "not identified or without rule",
                "- Falling back to default",
                opts.purpose,
                "rule",
            )
        except FPRule.DoesNotExist:
            job.print_output(
                "Not normalizing",
                os.path.basename(file_.currentlocation),
                " - No rule or default rule found to normalize for",
                opts.purpose,
            )
            return NO_RULE_FOUND

    job.print_output("Format Policy Rule:", rule)
    command = rule.command
    job.print_output("Format Policy Command", command.description)

    replacement_dict = get_replacement_dict(job, opts)
    cl = transcoder.CommandLinker(
        job, rule, command, replacement_dict, opts, once_normalized_callback(job)
    )
    exitstatus = cl.execute()

    # If the access/thumbnail normalization command has errored AND a
    # derivative was NOT created, then we run the default access/thumbnail
    # rule. Note that we DO need to check if the derivative file exists. Even
    # when a verification command exists for the normalization command, the
    # transcoder.py::Command.execute method will only run the verification
    # command if the normalization command returns a 0 exit code.
    # Errored thumbnail normalization also needs to result in default thumbnail
    # normalization; if not, then a transfer with a single file that failed
    # thumbnail normalization will result in a failed SIP at "Prepare DIP: Copy
    # thumbnails to DIP directory"
    if (
        exitstatus != 0
        and opts.purpose in ("access", "thumbnail")
        and cl.commandObject.output_location
        and (not os.path.isfile(cl.commandObject.output_location))
    ):
        # Fall back to default rule
        try:
            fallback_rule = get_default_rule(opts.purpose)
            job.print_output(
                opts.purpose,
                "normalization failed, falling back to default",
                opts.purpose,
                "rule",
            )
        except FPRule.DoesNotExist:
            job.print_output(
                "Not retrying normalizing for",
                os.path.basename(file_.currentlocation),
                " - No default rule found to normalize for",
                opts.purpose,
            )
            fallback_rule = None
        # Don't re-run the same command
        if fallback_rule and fallback_rule.command != command:
            job.print_output("Fallback Format Policy Rule:", fallback_rule)
            command = fallback_rule.command
            job.print_output("Fallback Format Policy Command", command.description)

            # Use existing replacement dict
            cl = transcoder.CommandLinker(
                job,
                fallback_rule,
                command,
                replacement_dict,
                opts,
                once_normalized_callback(job),
            )
            exitstatus = cl.execute()

    # Store thumbnails locally for use during AIP searches
    # TODO is this still needed, with the storage service?
    if "thumbnail" in opts.purpose:
        thumbnail_filepath = cl.commandObject.output_location
        thumbnail_storage_dir = os.path.join(
            mcpclient_settings.SHARED_DIRECTORY, "www", "thumbnails", opts.sip_uuid
        )
        try:
            os.makedirs(thumbnail_storage_dir)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(thumbnail_storage_dir):
                pass
            else:
                raise
        thumbnail_basename, thumbnail_extension = os.path.splitext(thumbnail_filepath)
        thumbnail_storage_file = os.path.join(
            thumbnail_storage_dir, opts.file_uuid + thumbnail_extension
        )

        shutil.copyfile(thumbnail_filepath, thumbnail_storage_file)

    if not exitstatus == 0:
        job.print_error("Command", command.description, "failed!")
        return RULE_FAILED
    else:
        job.print_output(
            "Successfully normalized ",
            os.path.basename(opts.file_path),
            "for",
            opts.purpose,
        )
        return SUCCESS


def call(jobs):
    parser = argparse.ArgumentParser(description="Identify file formats.")
    # sip dir
    parser.add_argument(
        "purpose", type=str, help='"preservation", "access", "thumbnail"'
    )
    parser.add_argument("file_uuid", type=str, help="%fileUUID%")
    parser.add_argument("file_path", type=str, help="%relativeLocation%")
    parser.add_argument("sip_path", type=str, help="%SIPDirectory%")
    parser.add_argument("sip_uuid", type=str, help="%SIPUUID%")
    parser.add_argument("task_uuid", type=str, help="%taskUUID%")
    parser.add_argument(
        "normalize_file_grp_use",
        type=str,
        help='"service", "original", "submissionDocumentation", etc',
    )
    parser.add_argument(
        "--thumbnail_mode",
        type=str,
        default="generate",
        help='"generate", "generate_non_default", "do_not_generate"',
    )

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                opts = parser.parse_args(job.args[1:])

                if (
                    opts.purpose == "thumbnail"
                    and opts.thumbnail_mode == "do_not_generate"
                ):
                    job.pyprint("Thumbnail generation has been disabled")
                    job.set_status(SUCCESS)
                    continue

                try:
                    job.set_status(main(job, opts))
                except Exception as e:
                    job.print_error(str(e))
                    job.set_status(1)
