#!/usr/bin/python2 -OO
from __future__ import print_function
import argparse
import ConfigParser
import csv
import datetime
import errno
import os
import shutil
import sys
import traceback
import uuid

import transcoder

# archivematicaCommon
import databaseFunctions
import fileOperations
from dicts import ReplacementDict

# dashboard
from fpr.models import FPRule
from main.models import Derivation, FileFormatVersion, File, FileID
from annoying.functions import get_object_or_None

# Return codes
SUCCESS = 0
RULE_FAILED = 1
NO_RULE_FOUND = 2

def get_replacement_dict(opts):
    """ Generates values for all knows %var% replacement variables. """
    prefix = ""
    postfix = ""
    output_dir = ""
    #get file name and extension
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
        print("Unsupported command purpose", opts.purpose, file=sys.stderr)
        return None

    # Populates the standard set of unit variables, so,
    # e.g., %fileUUID% is available
    replacement_dict = ReplacementDict.frommodel(type_='file',
                                                 file_=opts.file_uuid)

    output_filename = ''.join([prefix, filename, postfix])
    replacement_dict.update({
        "%outputDirectory%": output_dir,
        "%prefix%": prefix,
        "%postfix%": postfix,
        "%outputFileName%": output_filename, # does not include extension
        "%outputFilePath%": os.path.join(output_dir, output_filename) # does not include extension
    })
    return replacement_dict


def check_manual_normalization(opts):
    """ Checks for manually normalized file, returns that path or None. 

    Checks by looking for access/preservation files for a give original file.

    Check the manualNormalization/access and manualNormalization/preservation
    directories for access and preservation files.  If a nomalization.csv
    file is specified, check there first for the mapping between original
    file and access/preservation file. """

    # If normalization.csv provided, check there for mapping from original
    # to access/preservation file
    normalization_csv = os.path.join(opts.sip_path, "objects", "manualNormalization", "normalization.csv")
    # Get original name of target file, to handle sanitized names
    file_ = File.objects.get(uuid=opts.file_uuid)
    bname = file_.originallocation.replace('%transferDirectory%objects/', '', 1).replace('%SIPDirectory%objects/', '', 1)
    if os.path.isfile(normalization_csv):
        found = False
        # use universal newline mode to support unusual newlines, like \r
        with open(normalization_csv, 'rbU') as csv_file:
            reader = csv.reader(csv_file)
            # Search the file for an original filename that matches the one provided
            try:
                for row in reader:
                    if not row:
                        continue
                    if "#" in row[0]: # ignore comments
                        continue
                    original, access_file, preservation_file = row
                    if original == bname:
                        print('Filename', bname, 'matches entry in normalization.csv', original)
                        found = True
                        break
            except csv.Error:
                print("Error reading", normalization_csv, " on line", reader.line_num, file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return None

        # If we didn't find a match, let it fall through to the usual method
        if found:
            # No manually normalized file for command classification
            if "preservation" in opts.purpose and not preservation_file:
                return None
            if "access" in opts.purpose and not access_file:
                return None

            # If we found a match, verify access/preservation exists in DB
            # match and pull original location b/c sanitization
            if "preservation" in opts.purpose:
                filename = preservation_file
            elif "access" in opts.purpose:
                filename = access_file
            else:
                return None
            print('Looking for', filename, 'in database')
            # FIXME: SQL uses removedtime=0. Convince Django to express this
            return File.objects.get(sip=opts.sip_uuid, originallocation__iendswith=filename) #removedtime = 0

    # Assume that any access/preservation file found with the right
    # name is the correct one
    # Strip extension, replace SIP path with %var%
    path = os.path.splitext(opts.file_path.replace(opts.sip_path, '%SIPDirectory%', 1))[0]
    if "preservation" in opts.purpose:
        path = path.replace("%SIPDirectory%objects/",
            "%SIPDirectory%objects/manualNormalization/preservation/")
    elif "access" in opts.purpose:
        path = path.replace("%SIPDirectory%objects/",
            "%SIPDirectory%objects/manualNormalization/access/")
    else:
        return None
    try:
        # FIXME: SQL uses removedtime=0. Cannot get Django to express this
        return File.objects.get(sip=opts.sip_uuid, currentlocation__startswith=path) #removedtime = 0
    except (File.DoesNotExist, File.MultipleObjectsReturned):
        # No file with the correct path found, assume not manually normalized
        return None
    return None

def once_normalized(command, opts, replacement_dict):
    """ Updates the database if normalization completed successfully.

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
        for w in os.walk(command.output_location):
            path, _, files = w
            for p in files:
                p = os.path.join(path, p)
                if os.path.isfile(p):
                    transcoded_files.append(p)
    elif command.output_location:
        print("Error - output file does not exist [", command.output_location, "]", file=sys.stderr)
        command.exit_code = -2

    derivation_event_uuid = str(uuid.uuid4())
    event_detail_output = 'ArchivematicaFPRCommandID="{}"'.format(command.fpcommand.uuid)
    if command.event_detail_command is not None:
        event_detail_output += '; {}'.format(command.event_detail_command.std_out)
    for ef in transcoded_files:
        if "thumbnails" in opts.purpose:
            continue

        today = str(datetime.date.today())
        output_file_uuid = str(uuid.uuid4())
        # TODO Add manual normalization for files of same name mapping?
        #Add the new file to the SIP
        path_relative_to_sip = ef.replace(opts.sip_path, "%SIPDirectory%", 1)
        fileOperations.addFileToSIP(
            path_relative_to_sip,
            output_file_uuid, # File UUID
            opts.sip_uuid, # SIP UUID
            opts.task_uuid, # Task UUID
            today, # Current date
            sourceType="creation",
            use=opts.purpose,
        )

        #Calculate new file checksum
        fileOperations.updateSizeAndChecksum(
            output_file_uuid, # File UUID, same as task UUID for preservation
            ef, # File path
            today, # Date
            str(uuid.uuid4()), # Event UUID, new UUID
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
                event=None
            )
            d.save()

        # Use the format info from the normalization command
        # to save identification into the DB
        ffv = FileFormatVersion(
            file_uuid_id=output_file_uuid,
            format_version=command.fpcommand.output_format
        )
        ffv.save()

        FileID.objects.create(
            file_id=output_file_uuid,
            format_name=command.fpcommand.output_format.description
        )


def insert_derivation_event(original_uuid, output_uuid, derivation_uuid,
        event_detail_output, outcome_detail_note, today=None):
    """ Add the derivation link for preservation files and the event. """
    if today is None:
        today = str(datetime.date.today())
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
    return FPRule.active.get(purpose='default_'+purpose)

def main(opts):
    """ Find and execute normalization commands on input file. """
    # TODO fix for maildir working only on attachments

    # Find the file and it's FormatVersion (file identification)
    try:
        file_ = File.objects.get(uuid=opts.file_uuid)
    except File.DoesNotExist:
        print('File with uuid', opts.file_uuid, 'does not exist in database.', file=sys.stderr)
        return NO_RULE_FOUND
    print('File found:', file_.uuid, file_.currentlocation)

    # Unless normalization file group use is submissionDocumentation, skip the
    # submissionDocumentation directory
    if opts.normalize_file_grp_use != "submissionDocumentation" and file_.currentlocation.startswith('%SIPDirectory%objects/submissionDocumentation'):
        print('File', os.path.basename(opts.file_path), 'in objects/submissionDocumentation, skipping')
        return SUCCESS

    # Only normalize files where the file's group use and normalize group use match
    if file_.filegrpuse != opts.normalize_file_grp_use:
        print(os.path.basename(opts.file_path), 'is file group usage', file_.filegrpuse, 'instead of ', opts.normalize_file_grp_use, ' - skipping')
        return SUCCESS

    # If a file has been manually normalized for this purpose, skip it
    manually_normalized_file = check_manual_normalization(opts)
    if manually_normalized_file:
        print(os.path.basename(opts.file_path), 'was already manually normalized into', manually_normalized_file.currentlocation)
        if 'preservation' in opts.purpose:
            # Add derivation link and associated event
            insert_derivation_event(
                original_uuid=opts.file_uuid,
                output_uuid=manually_normalized_file.uuid,
                derivation_uuid=str(uuid.uuid4()),
                event_detail_output="manual normalization",
                outcome_detail_note=None,
            )
        return SUCCESS

    format_id = get_object_or_None(
        FileFormatVersion,
        file_uuid=opts.file_uuid
    )

    # Look up the normalization command in the FPR
    if format_id is None:
        rule = get_default_rule(opts.purpose)
        print(os.path.basename(file_.currentlocation), "not identified - falling back to default", opts.purpose, "rule")
    else:
        print('File format:', format_id.format_version)
        try:
            rule = FPRule.active.get(format=format_id.format_version,
                                     purpose=opts.purpose)
        except FPRule.DoesNotExist:
            try:
                rule = get_default_rule(opts.purpose)
                print("No rule for", os.path.basename(file_.currentlocation),
                    "falling back to default", opts.purpose, "rule")
            except FPRule.DoesNotExist:
                print('Not normalizing', os.path.basename(file_.currentlocation),
                    ' - No rule or default rule found to normalize for', opts.purpose,
                    file=sys.stderr)
                return NO_RULE_FOUND
    print('Format Policy Rule:', rule)
    command = rule.command
    print('Format Policy Command', command.description)

    replacement_dict = get_replacement_dict(opts)
    cl = transcoder.CommandLinker(rule, command, replacement_dict, opts, once_normalized)
    exitstatus = cl.execute()

    # Store thumbnails locally for use during AIP searches
    # TODO is this still needed, with the storage service?
    if 'thumbnail' in opts.purpose:
        thumbnail_filepath = cl.commandObject.output_location
        clientConfigFilePath = '/etc/archivematica/MCPClient/clientConfig.conf'
        config = ConfigParser.SafeConfigParser()
        config.read(clientConfigFilePath)
        try:
            shared_path = config.get('MCPClient', 'sharedDirectoryMounted')
        except:
            shared_path = '/var/archivematica/sharedDirectory/'
        thumbnail_storage_dir = os.path.join(
            shared_path,
            'www',
            'thumbnails',
            opts.sip_uuid,
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
            thumbnail_storage_dir,
            opts.file_uuid + thumbnail_extension,
        )

        shutil.copyfile(thumbnail_filepath, thumbnail_storage_file)

    if not exitstatus == 0:
        print('Command', command.description, 'failed!', file=sys.stderr)
        return RULE_FAILED
    else:
        print('Successfully normalized ', os.path.basename(opts.file_path), 'for', opts.purpose)
        return SUCCESS


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Identify file formats.')
    # sip dir
    parser.add_argument('purpose', type=str, help='"preservation", "access", "thumbnail"')
    parser.add_argument('file_uuid', type=str, help='%fileUUID%')
    parser.add_argument('file_path', type=str, help='%relativeLocation%')
    parser.add_argument('sip_path', type=str, help='%SIPDirectory%')
    parser.add_argument('sip_uuid', type=str, help='%SIPUUID%')
    parser.add_argument('task_uuid', type=str, help='%taskUUID%')
    parser.add_argument('normalize_file_grp_use', type=str, help='"service", "original", "submissionDocumentation", etc')

    opts = parser.parse_args()
    sys.exit(main(opts))

