#!/usr/bin/python -OO
import ConfigParser
import os
import shutil
import sys

# archivematicaCommon
from executeOrRunSubProcess import executeOrRun


def extract_aip(aip_path, extract_path):
    os.makedirs(extract_path)
    command = "atool --extract-to={} -V0 {}".format(extract_path, aip_path)
    print 'Running extraction command:', command
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

    clientConfigFilePath = '/etc/archivematica/MCPClient/clientConfig.conf'
    config = ConfigParser.SafeConfigParser()
    config.read(clientConfigFilePath)
    temp_dir = config.get('MCPClient', 'temp_dir')

    is_uncompressed_aip = os.path.isdir(aip_path)

    if is_uncompressed_aip:
        bag = aip_path
    else:
        try:
            extract_dir = os.path.join(temp_dir, sip_uuid)
            bag = extract_aip(aip_path, extract_dir)
        except Exception:
            print >>sys.stderr, 'Error extracting AIP at "{}"'.format(aip_path)
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
        print "Running test: ", command
        exit_code, _, _ = executeOrRun("command", command, printing=True)
        if exit_code != 0:
            print >>sys.stderr, "Failed test: ", command
            return_code = 1
    #cleanup
    if not is_uncompressed_aip:
        shutil.rmtree(extract_dir)
    return return_code

if __name__ == '__main__':
    sys.exit(verify_aip())
