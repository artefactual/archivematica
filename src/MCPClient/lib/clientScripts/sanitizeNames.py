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

import string
import os
from shutil import move as rename
import sys
from unidecode import unidecode

VERSION = "1.10." + "$Id$".split(" ")[1]
VALID = "-_.()" + string.ascii_letters + string.digits
REPLACEMENT_CHAR = "_"


def transliterate(basename):
    # We get a more meaningful name sanitization if UTF-8 names
    # are correctly decoded to unistrings instead of str
    try:
        return unidecode(basename.decode('utf-8'))
    except UnicodeDecodeError:
        return unidecode(basename)


def sanitizeName(basename):
    """Replace all chars in ``basename`` with ``REPLACEMENT_CHAR`` except ASCII
    chars defined in ``VALID``.
    """
    ret = []
    basename = transliterate(basename)
    for c in basename:
        if c in VALID:
            ret.append(c)
        else:
            ret.append(REPLACEMENT_CHAR)
    return ''.join(ret).encode('utf-8')


def debug_sanitization(path, dirname, basename, sanitizedName):
    print "path: " + path
    print "dirname: " + dirname
    print "basename: " + basename
    print "sanitizedName: " + sanitizedName
    print "renamed:", basename != sanitizedName


def sanitizePath(path):
    """Sanitize the basename of ``path`` and move the file at ``path`` to the
    newly sanitized path.
    """
    basename = os.path.basename(path)
    dirname = os.path.dirname(path)
    sanitizedName = sanitizeName(basename)
    if False:
        debug_sanitization(path, dirname, basename, sanitizedName)
    if basename == sanitizedName:
        return path
    else:
        sanitizedName = get_unique_sanitized_name(sanitizedName, dirname)
        rename(path, sanitizedName)
        return sanitizedName


def get_unique_sanitized_name(sanitizedName, dirname):
    """Append successively higher ints to ``sanitizedName`` in ``dirname``
    until the former is unique in the latter.
    """
    s = sanitizedName
    index = s.rfind('.')
    fileTitle = sanitizedName
    if index != -1:
        fileTitle = s[:index]
    fileExtension = s.split(".")[-1]
    if fileExtension != sanitizedName:
        fileExtension = "." + fileExtension
    else:
        fileExtension = ""
    sanitizedName = os.path.join(dirname, '%s%s' % (fileTitle, fileExtension))
    n = 1
    while os.path.exists(sanitizedName):
        new_name = '%s%s%s%s' % (fileTitle, REPLACEMENT_CHAR, n,
                                 fileExtension)
        sanitizedName = os.path.join(dirname, new_name)
        n += 1
    return sanitizedName


def sanitizeRecursively(path):
    """Sanitize ``path`` and all of its sub-paths. Return a list of tuples,
    each containing the original path and its sanitized counterpart.
    """
    path = os.path.abspath(path)
    sanitizations = []
    sanitizedName = sanitizePath(path)
    if sanitizedName != path:
        sanitizations.append((path, sanitizedName))
    if os.path.isdir(sanitizedName):
        for f in os.listdir(sanitizedName):
            new_path = os.path.join(sanitizedName, f)
            sanitizations.extend(sanitizeRecursively(new_path))
    return sanitizations


if __name__ == '__main__':
    if len(sys.argv) != 2:
        msg = "Error, sanitizeNames takes one agrument PATH or -V (version)"
        print >>sys.stderr, msg
        quit(-1)
    path = sys.argv[1]
    if path == "-V":
        print VERSION
        quit(0)
    if not os.path.isdir(path):
        print >>sys.stderr, "Not a directory: %s" % path
        quit(-1)
    print "Scanning: %s" % path
    sanitizations = sanitizeRecursively(path)
    for oldfile, newfile in sanitizations:
        print "%s -> %s" % (oldfile, newfile)
    print >>sys.stderr, "TEST DEBUG CLEAR DON'T INCLUDE IN RELEASE"
