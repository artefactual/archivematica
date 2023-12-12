#!/usr/bin/env python
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
import re
import shutil

from unidecode import unidecode

VERSION = "1.10." + "$Id$".split(" ")[1]

# Letters, digits and a few punctuation characters
ALLOWED_CHARS = re.compile(r"[^a-zA-Z0-9\-_.\(\)]")
REPLACEMENT_CHAR = "_"


def change_name(basename):
    if basename == "":
        raise ValueError("change_name received an empty filename.")
    decoded_name = unidecode(basename)
    # We can't return  an empty string here because it will become the new filename.
    # However, in some cases unidecode just strips out all chars (e.g.
    # unidecode(u"🚀") == ""), so if that happens, we to replace the invalid chars with
    # REPLACEMENT_CHAR. This will result in a filename of one or more underscores,
    # which isn't great, but allows processing to continue.
    if decoded_name == "":
        decoded_name = basename

    return ALLOWED_CHARS.sub(REPLACEMENT_CHAR, decoded_name)


def change_path(path, max_filename):
    basename = os.path.basename(path)
    changed_name = change_name(basename)

    if basename == changed_name:
        return path

    dirname = os.path.dirname(path)

    n = 1
    file_title, file_extension = os.path.splitext(changed_name)
    max_file_title = max_filename - len(file_extension)
    changed_name = os.path.join(dirname, file_title[:max_file_title] + file_extension)

    while os.path.exists(changed_name):
        changed_name = os.path.join(
            dirname,
            file_title[: max_file_title - (len(REPLACEMENT_CHAR) + len(str(n)))]
            + REPLACEMENT_CHAR
            + str(n)
            + file_extension,
        )
        n += 1
    shutil.move(path, changed_name)

    return changed_name


def change_tree(start_path, old_start_path):
    """
    Recursive generator to change all filesystem entries under the start
    path given.

    Yields a tuple of (old_path, changed_path, is_dir, was_changed) once
    for each file or dir within the start_path, everything contained in each
    dir.
    """
    start_path = os.path.abspath(start_path)
    max_filename = os.pathconf(start_path, "PC_NAME_MAX")

    for dir_entry in os.scandir(start_path):
        is_dir = dir_entry.is_dir()  # cache is_dir before rename

        changed_name = change_path(dir_entry.path, max_filename)
        changed_path = os.path.join(start_path, changed_name)
        old_path = os.path.join(old_start_path, dir_entry.name)

        was_changed = changed_path != old_path
        yield old_path, changed_path, is_dir, was_changed

        if is_dir:
            yield from change_tree(changed_path, old_path)
