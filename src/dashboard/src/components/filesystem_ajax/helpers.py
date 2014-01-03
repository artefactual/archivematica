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

import os
from subprocess import call
import logging

import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivematicaFunctions
from components import helpers

# for unciode sorting support
import locale
locale.setlocale(locale.LC_ALL, '')

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematicaDashboard.log",
    level=logging.INFO)

def rsync_copy(source, destination):
    call([
        'rsync',
        '-r',
        '-t',
        source,
        destination
    ])

def sorted_directory_list(path):
    cleaned = []
    entries = os.listdir(archivematicaFunctions.unicodeToStr(path))
    cleaned = [archivematicaFunctions.unicodeToStr(entry) for entry in entries]
    return sorted(cleaned, key=helpers.keynat)

def directory_to_dict(path, directory={}, entry=False):
    # if starting traversal, set entry to directory root
    if (entry == False):
        entry = directory
        # remove leading slash
        entry['parent'] = os.path.dirname(path)[1:]

    # set standard entry properties
    entry['name'] = os.path.basename(path)
    entry['children'] = []

    # define entries
    entries = sorted_directory_list(path)
    for file in entries:
        new_entry = None
        if file[0] != '.':
            new_entry = {}
            new_entry['name'] = file
            entry['children'].append(new_entry)

        # if entry is a directory, recurse
        child_path = os.path.join(path, file)
        if new_entry != None and os.path.isdir(child_path) and os.access(child_path, os.R_OK):
            directory_to_dict(child_path, directory, new_entry)

    # return fully traversed data
    return directory

def directory_contents(path, contents=[]):
    entries = sorted_directory_list(path)
    for entry in entries:
        contents.append(os.path.join(path, entry))
        entry_path = os.path.join(path, entry)
        if os.path.isdir(entry_path) and os.access(entry_path, os.R_OK):
            directory_contents(entry_path, contents)
    return contents

def check_filepath_exists(filepath):
    error = None
    if filepath == '':
        error = 'No filepath provided.'

    # check if exists
    if error == None and not os.path.exists(filepath):
        error = 'Filepath ' + filepath + ' does not exist.'

    # check if is file or directory

    # check for trickery
    try:
        filepath.index('..')
        error = 'Illegal path.'
    except:
        pass

    return error
