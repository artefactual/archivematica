#!/usr/bin/python -OO
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

import argparse
import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun


def run_bag(arguments):
    """ Run Bagit's create bag command. """
    command = "/usr/share/bagit/bin/bag {}".format(arguments)
    print 'Command to run:', command
    exit_code, std_out, std_err = executeOrRun("command", command, printing=False)
    if exit_code != 0:
        print >> sys.stderr, "Error with command: ", command
        print >> sys.stderr, "Standard OUT:"
        print >> sys.stderr, std_out
        print >> sys.stderr, "Standard Error:"
        print >> sys.stderr, std_err
        exit(exit_code)
    else:
        print std_out
        print >> sys.stderr, std_err

def get_sip_directories(sip_dir):
    """ Get a list of directories in the SIP, to be created after bagged. """
    directory_list = []
    for directory, subdirs, _ in os.walk(sip_dir):
        for subdir in subdirs:
            path = os.path.join(directory, subdir).replace(sip_dir + "/", "", 1)
            directory_list.append(path)
    print "directory list:"
    for sip_dir in directory_list:
        print "\t", sip_dir
    return directory_list

def create_directories(base_dir, dir_list):
    """ Create all the SIP's directories in the bag's data/ folder.

    Some directories should have been created in the data/ folder by the bagit
    command, but create any empty (or unspecified) directories. """
    for directory in dir_list:
        directory = os.path.join(base_dir, directory)
        try:
            os.makedirs(directory)
        except os.error:
            pass

def bag_with_empty_directories(args):
    """ Run bagit create bag command, and create any empty directories from the SIP. """
    # Get list of directories in SIP
    sip_dir = os.path.dirname(args.destination)
    dir_list = get_sip_directories(sip_dir)

    # Ensure all payload items actually exist
    payload_entries = [e for e in args.payload_entries if os.path.exists(e)]
    payload_entries = ' '.join('"{}"'.format(d) for d in payload_entries)

    # Reconstruct bagit arguments
    bagit_args = [args.operation, '"{}"'.format(args.destination), payload_entries, '--writer', args.writer, '--payloadmanifestalgorithm', args.algorithm]
    bagit_args = ' '.join(bagit_args)

    # Run bagit bag creator
    run_bag(bagit_args)
    create_directories(os.path.join(args.destination, "data"), dir_list)

if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(description='Convert folder into a bag.')
    parser.add_argument('operation')
    parser.add_argument('destination')
    parser.add_argument('payload_entries', metavar='Payload', nargs='+',
                   help='All the files/folders that should go in the bag.')
    parser.add_argument('--writer', dest='writer')
    parser.add_argument('--payloadmanifestalgorithm', dest='algorithm')
    args = parser.parse_args()
    bag_with_empty_directories(args)
