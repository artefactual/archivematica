#!/usr/bin/env python2
# -*- coding: utf8
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
# @subpackage MCPClient
# @author Joseph Perry <joseph@artefactual.com>

import os
import re
import shutil

from scandir import scandir
from unidecode import unidecode

from archivematicaFunctions import strToUnicode

VERSION = "1.10." + "$Id$".split(" ")[1]

# Letters, digits and a few punctuation characters
ALLOWED_CHARS = re.compile(r"[^a-zA-Z0-9\-_.\(\)]")
REPLACEMENT_CHAR = "_"


def sanitize_name(basename):
    if basename == "":
        raise ValueError("sanitize_name recieved an empty filename.")
    unicode_basename = strToUnicode(basename)
    unicode_name = unidecode(unicode_basename)
    # We can't return  an empty string here because it will become the new filename.
    # However, in some cases unidecode just strips out all chars (e.g.
    # unidecode(u"🚀") == ""), so if that happens, we to replace the invalid chars with
    # REPLACEMENT_CHAR. This will result in a filename of one or more underscores,
    # which isn't great, but allows processing to continue.
    if unicode_name == "":
        unicode_name = unicode_basename

    return ALLOWED_CHARS.sub(REPLACEMENT_CHAR, unicode_name)


def sanitize_path(path):
    basename = os.path.basename(path)
    sanitized_name = sanitize_name(basename)

    if basename == sanitized_name:
        return path

    dirname = os.path.dirname(path)

    n = 1
    file_title, file_extension = os.path.splitext(sanitized_name)
    sanitized_name = os.path.join(dirname, file_title + file_extension)

    while os.path.exists(sanitized_name):
        sanitized_name = os.path.join(
            dirname, file_title + REPLACEMENT_CHAR + str(n) + file_extension
        )
        n += 1
    shutil.move(path, sanitized_name)

    return sanitized_name


def sanitize_tree(start_path, old_start_path):
    """
    Recursive generator to sanitize all filesystem entries under the start
    path given.

    Yields a tuple of (old_path, sanitized_path, is_dir, was_sanitized) once
    for each file or dir within the start_path, everything contained in each
    dir.
    """
    start_path = os.path.abspath(start_path)

    for dir_entry in scandir(start_path):
        is_dir = dir_entry.is_dir()  # cache is_dir before rename

        sanitized_name = sanitize_path(dir_entry.path)
        sanitized_path = os.path.join(start_path, sanitized_name)
        old_path = os.path.join(old_start_path, dir_entry.name)

        was_sanitized = sanitized_path != old_path
        yield old_path, sanitized_path, is_dir, was_sanitized

        if is_dir:
            for result in sanitize_tree(sanitized_path, old_path):
                yield result
