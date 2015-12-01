import base64
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

logger = logging.getLogger('archivematica.dashboard')

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
        entry['parent'] = base64.b64encode(os.path.dirname(path)[1:])

    # set standard entry properties
    entry['name'] = base64.b64encode(os.path.basename(path))
    entry['children'] = []

    # define entries
    entries = sorted_directory_list(path)
    for file in entries:
        new_entry = None
        if file[0] != '.':
            new_entry = {}
            new_entry['name'] = base64.b64encode(file)
            entry['children'].append(new_entry)

        # if entry is a directory, recurse
        child_path = os.path.join(path, file)
        if new_entry != None and os.path.isdir(child_path) and os.access(child_path, os.R_OK):
            directory_to_dict(child_path, directory, new_entry)

    # return fully traversed data
    return directory

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
