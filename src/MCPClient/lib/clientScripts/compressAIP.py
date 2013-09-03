#!/usr/bin/python2

import argparse
import os.path
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from executeOrRunSubProcess import executeOrRun


def compress_aip(compression, compression_level, sip_directory, sip_name, sip_uuid):
    """ Compresses AIP according to compression algorithm and level.
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
        program, compression_algorithm = compression.split('-')
    except ValueError:
        msg = "Invalid program-compression algorithm: {}".format(compression)
        print >> sys.stderr, msg
        return -1

    archive_path = '{name}-{uuid}'.format(name=sip_name, uuid=sip_uuid)
    uncompressed_location = sip_directory+archive_path

    print "Compressing {} with {}, algorithm {}, level {}".format(
        uncompressed_location, program, compression_algorithm, compression_level)

    if program == '7z':
        compressed_location = uncompressed_location+".7z"
        command = '/usr/bin/7z a -bd -t7z -y -m0={algorithm} -mx={level} -mta=on -mtc=on -mtm=on -mmt=on "{compressed_location}" "{uncompressed_location}"'.format(
            algorithm=compression_algorithm, level=compression_level,
            uncompressed_location=uncompressed_location,
            compressed_location=compressed_location
        )
    elif program == 'pbzip2':
        compressed_location = uncompressed_location+".tar.bz2"
        command = '/bin/tar -c --directory "{sip_directory}" "{archive_path}" | /usr/bin/pbzip2 --compress -{level} > "{compressed_location}"'.format(
            sip_directory=sip_directory, archive_path=archive_path,
            level=compression_level, compressed_location=compressed_location
        )
    else:
        msg = "Program {} not recognized, exiting script prematurely.".format(program)
        print >> sys.stderr, msg
        return -1

    print 'Executing command: {}'.format(command)
    exit_code, _, _ = executeOrRun("bashScript", command, printing=True)

    # Set aipFilename in Unit
    sql = """ UPDATE SIPs SET aipFilename='{aipFilename}' WHERE sipUUID='{sip_uuid}';""".format(
        aipFilename=os.path.basename(compressed_location),
        sip_uuid=sip_uuid)
    databaseInterface.runSQL(sql)

    return exit_code

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compress an AIP.')
    parser.add_argument('compression', type=str, help='%AIPCompressionAlgorithm%')
    parser.add_argument('compression_level', type=str, help='%AIPCompressionLevel%')
    parser.add_argument('sip_directory', type=str, help='%SIPDirectory%')
    parser.add_argument('sip_name', type=str, help='%SIPName%')
    parser.add_argument('sip_uuid', type=str, help='%SIPUUID%')
    args = parser.parse_args()
    sys.exit(compress_aip(args.compression, args.compression_level,
        args.sip_directory, args.sip_name, args.sip_uuid))
