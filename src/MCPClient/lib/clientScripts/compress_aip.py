#!/usr/bin/env python
import argparse
import os.path
import sys

import django
from django.db import transaction

django.setup()


import databaseFunctions
from executeOrRunSubProcess import executeOrRun
from main.models import SIP


def update_unit(sip_uuid, compressed_location):
    # Set aipFilename in Unit
    SIP.objects.filter(uuid=sip_uuid).update(
        aip_filename=os.path.basename(compressed_location)
    )


def compress_aip(
    job, compression, compression_level, sip_directory, sip_name, sip_uuid
):
    """Compresses AIP according to compression algorithm and level.
    compression = AIP compression algorithm, format: <program>-<algorithm>, eg. 7z-lzma, pbzip2-
    compression_level = AIP compression level, integer between 1 and 9 inclusive
    sip_directory = Absolute path to the directory where the SIP is
    sip_name = User-provided name of the SIP
    sip_uuid = SIP UUID

    Example inputs:
    compressAIP.py
        7z-lzma
        5
        /var/archivematica/sharedDirectory/watchedDirectories/workFlowDecisions/compressionAIPDecisions/ep-d87d5845-bd07-4200-b1a4-928e0cb6e1e4/
        ep
        d87d5845-bd07-4200-b1a4-928e0cb6e1e4
    """
    try:
        program, compression_algorithm = compression.split("-")
    except ValueError:
        msg = f"Invalid program-compression algorithm: {compression}"
        job.pyprint(msg, file=sys.stderr)
        return 255, {}

    archive_path = f"{sip_name}-{sip_uuid}"
    uncompressed_location = sip_directory + archive_path

    # Even though no actual compression is taking place,
    # the location still needs to be set in the unit to ensure that the
    # %AIPFilename% variable is set appropriately.
    # Setting it to an empty string ensures the common
    # "%SIPDirectory%%AIPFilename%" pattern still points at the right thing.
    if program == "None":
        return 0, {"sip_uuid": sip_uuid, "location": uncompressed_location}

    job.pyprint(
        f"Compressing {uncompressed_location} with {program}, algorithm {compression_algorithm}, level {compression_level}"
    )

    if program == "7z":
        compressed_location = uncompressed_location + ".7z"
        command = f'/usr/bin/7z a -bd -t7z -y -m0={compression_algorithm} -mx={compression_level} -mta=on -mtc=on -mtm=on -mmt=on "{compressed_location}" "{uncompressed_location}"'
        tool_info_command = (
            r'echo program="7z"\; '
            rf'algorithm="{compression_algorithm}"\; '
            'version="`7z | grep Version`"'
        )
    elif program == "pbzip2":
        compressed_location = uncompressed_location + ".tar.bz2"
        command = f'/bin/tar -c --directory "{sip_directory}" "{archive_path}" | /usr/bin/pbzip2 --compress -{compression_level} > "{compressed_location}"'
        tool_info_command = (
            r'echo program="pbzip2"\; '
            rf'algorithm="{compression_algorithm}"\; '
            'version="$((pbzip2 -V) 2>&1)"'
        )
    elif program == "gzip":
        compressed_location = uncompressed_location + ".tar.gz"
        command = f'/bin/tar -c --directory "{sip_directory}" "{archive_path}" | /bin/gzip -{compression_level} > "{compressed_location}"'
        tool_info_command = (
            r'echo program="gzip"\; '
            rf'algorithm="{compression_algorithm}"\; '
            'version="$((gzip -V) 2>&1)"'
        )
    else:
        msg = f"Program {program} not recognized, exiting script prematurely."
        job.pyprint(msg, file=sys.stderr)
        return 255, {}

    result = {"sip_uuid": sip_uuid, "location": compressed_location}

    job.pyprint("Executing command:", command)
    exit_code, std_out, std_err = executeOrRun(
        "bashScript", command, printing=True, capture_output=True
    )
    job.write_output(std_out)
    job.write_error(std_err)

    # Add new AIP File
    file_uuid = sip_uuid
    result["file"] = {
        "file_uuid": file_uuid,
        "file_path": compressed_location.replace(sip_directory, "%SIPDirectory%", 1),
        "sip_uuid": sip_uuid,
        "use": "aip",
    }

    # Add compression event
    job.pyprint("Tool info command:", tool_info_command)
    _, tool_info, tool_info_err = executeOrRun(
        "bashScript", tool_info_command, printing=True, capture_output=True
    )
    job.write_output(tool_info)
    job.write_error(tool_info_err)
    tool_output = f'Standard Output="{std_out}"; Standard Error="{std_err}"'
    result["event"] = {
        "event_type": "compression",
        "event_detail": tool_info,
        "event_outcome_detail_note": tool_output,
        "file_uuid": file_uuid,
    }

    return exit_code, result


def call(jobs):
    parser = argparse.ArgumentParser(description="Compress an AIP.")
    parser.add_argument("compression", type=str, help="%AIPCompressionAlgorithm%")
    parser.add_argument("compression_level", type=str, help="%AIPCompressionLevel%")
    parser.add_argument("sip_directory", type=str, help="%SIPDirectory%")
    parser.add_argument("sip_name", type=str, help="%SIPName%")
    parser.add_argument("sip_uuid", type=str, help="%SIPUUID%")

    state = []

    for job in jobs:
        with job.JobContext():
            args = parser.parse_args(job.args[1:])
            status, result = compress_aip(
                job,
                args.compression,
                args.compression_level,
                args.sip_directory,
                args.sip_name,
                args.sip_uuid,
            )
            job.set_status(status)
            if result:
                state.append(result)

    with transaction.atomic():
        for result in state:
            update_unit(result["sip_uuid"], result["location"])
            if "file" in result:
                databaseFunctions.insertIntoFiles(
                    fileUUID=result["file"]["file_uuid"],
                    filePath=result["file"]["file_path"],
                    sipUUID=result["file"]["sip_uuid"],
                    use=result["file"]["use"],
                )
            if "event" in result:
                databaseFunctions.insertIntoEvents(
                    eventType=result["event"]["event_type"],
                    eventDetail=result["event"]["event_detail"],
                    eventOutcomeDetailNote=result["event"]["event_outcome_detail_note"],
                    fileUUID=result["event"]["file_uuid"],
                )
