#!/usr/bin/env python2

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

from __future__ import print_function
import string
import os
from shutil import move as rename
import sys
import unicodedata
from unidecode import unidecode
from archivematicaFunctions import unicodeToStr

VERSION = "1.10." + "$Id$".split(" ")[1]
valid = "-_.()" + string.ascii_letters + string.digits
not_valid = ":"
replacementChar = "_"


def transliterate(basename):
    # We get a more meaningful name sanitization if UTF-8 names
    # are correctly decoded to unistrings instead of str
    try:
        return unidecode(basename.decode('utf-8'))
    except UnicodeDecodeError:
        return unidecode(basename)


def sanitizeName(basename):
    ret = ""
    basename = transliterate(basename)
    for c in basename:
        if (c in valid and c not in not_valid):
            ret += c
        else:
            ret += replacementChar
    return ret.encode('utf-8')


def sanitizePath(path):
    basename = os.path.basename(path)
    dirname = os.path.dirname(path)
    sanitizedName = sanitizeName(basename)

    if basename == sanitizedName:
        return path
    else:
        n = 1
        fileTitle, fileExtension = os.path.splitext(sanitizedName)
        sanitizedName = os.path.join(dirname, fileTitle + fileExtension)

        while os.path.exists(sanitizedName):
            sanitizedName = os.path.join(dirname, fileTitle + replacementChar + str(n) + fileExtension)
            n += 1
        rename(path, sanitizedName)
        return sanitizedName


def sanitizeRecursively(path):
    path = os.path.abspath(path)
    sanitizations = {}

    sanitizedName = sanitizePath(path)
    if sanitizedName != path:
        path_key = unicodeToStr(
            unicodedata.normalize('NFC', path.decode('utf8')))
        sanitizations[path_key] = sanitizedName
    if os.path.isdir(sanitizedName):
        for f in os.listdir(sanitizedName):
            sanitizations.update(sanitizeRecursively(os.path.join(sanitizedName, f)))

    return sanitizations


if __name__ == '__main__':
    path = sys.argv[1]
    if not os.path.isdir(path):
        print("Not a directory: " + path, file=sys.stderr)
        sys.exit(-1)
    print("Scanning: ", path)
    sanitizations = sanitizeRecursively(path)
    for oldfile, newfile in sanitizations.items():
        print(oldfile, " -> ", newfile)
    print("TEST DEBUG CLEAR DON'T INCLUDE IN RELEASE", file=sys.stderr)
