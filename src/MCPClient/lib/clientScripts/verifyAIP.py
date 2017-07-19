#!/usr/bin/env python2
from __future__ import print_function
import os
import shutil
import sys

# archivematicaCommon
from custom_handlers import get_script_logger
from executeOrRunSubProcess import executeOrRun

import django
django.setup()
from django.conf import settings as mcpclient_settings


def extract_aip(aip_path, extract_path):
    os.makedirs(extract_path)
    command = "atool --extract-to={} -V0 {}".format(extract_path, aip_path)
    print('Running extraction command:', command)
    exit_code, _, _ = executeOrRun("command", command, printing=True)
    if exit_code != 0:
        raise Exception("Error extracting AIP")

    aip_identifier, ext = os.path.splitext(os.path.basename(aip_path))
    if ext in ('.bz2', '.gz'):
        aip_identifier, _ = os.path.splitext(aip_identifier)
    return os.path.join(extract_path, aip_identifier)


def verify_aip():
    """ Verify the AIP was bagged correctly by extracting it and running verification on its contents.

    sys.argv[1] = UUID
      UUID of the SIP, which will become the UUID of the AIP
    sys.argv[2] = current location
      Full absolute path to the AIP's current location on the local filesystem
    """

    sip_uuid = sys.argv[1]  # %sip_uuid%
    aip_path = sys.argv[2]  # SIPDirectory%%sip_name%-%sip_uuid%.7z

    temp_dir = mcpclient_settings.TEMP_DIRECTORY

    is_uncompressed_aip = os.path.isdir(aip_path)

    if is_uncompressed_aip:
        bag = aip_path
    else:
        try:
            extract_dir = os.path.join(temp_dir, sip_uuid)
            bag = extract_aip(aip_path, extract_dir)
        except Exception:
            print('Error extracting AIP at "{}"'.format(aip_path), file=sys.stderr)
            return 1

    verification_commands = [
        '/usr/share/bagit/bin/bag verifyvalid "{}"'.format(bag),
        '/usr/share/bagit/bin/bag checkpayloadoxum "{}"'.format(bag),
        '/usr/share/bagit/bin/bag verifycomplete "{}"'.format(bag),
        '/usr/share/bagit/bin/bag verifypayloadmanifests "{}"'.format(bag),
        '/usr/share/bagit/bin/bag verifytagmanifests "{}"'.format(bag),
    ]
    return_code = 0
    for command in verification_commands:
        print("Running test: ", command)
        exit_code, _, _ = executeOrRun("command", command, printing=True)
        if exit_code != 0:
            print("Failed test: ", command, file=sys.stderr)
            return_code = 1
    # cleanup
    if not is_uncompressed_aip:
        shutil.rmtree(extract_dir)
    return return_code


if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.verifyAIP")

    sys.exit(verify_aip())
