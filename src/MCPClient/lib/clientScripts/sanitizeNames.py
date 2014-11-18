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
# @subpackage MCPClient
# @author Joseph Perry <joseph@artefactual.com>

import string
import os
from shutil import move as rename
import sys
from unidecode import unidecode

VERSION = "1.10." + "$Id$".split(" ")[1]
valid = "-_.()" + string.ascii_letters + string.digits
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
        if c in valid:
            ret += c
        else:
            ret += replacementChar
    return ret.encode('utf-8')

def sanitizePath(path):
    basename = os.path.basename(path)
    dirname = os.path.dirname(path)
    sanitizedName = sanitizeName(basename)
    if False:
        print "path: " + path
        print "dirname: " + dirname
        print "basename: " + basename
        print "sanitizedName: " + sanitizedName
        print "renamed:", basename != sanitizedName
    if basename == sanitizedName:
        return path
    else:
        n = 1
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
        sanitizedName = dirname + "/" + fileTitle + fileExtension

        while os.path.exists(sanitizedName):
            sanitizedName = dirname + "/" + fileTitle + replacementChar + n.__str__() + fileExtension
            n+=1
        rename(path, sanitizedName)
        return sanitizedName

def sanitizeRecursively(path):
    path = os.path.abspath(path)
    sanitizations = []

    sanitizedName = sanitizePath(path)
    if sanitizedName != path:
        sanitizations.append((path, sanitizedName))
    if os.path.isdir(sanitizedName):
        for f in os.listdir(sanitizedName):
            sanitizations.extend(sanitizeRecursively(sanitizedName + "/" + f))

    return sanitizations

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >>sys.stderr, "Error, sanitizeNames takes one agrument PATH or -V (version)"
        quit(-1)
    path = sys.argv[1]
    if path == "-V":
        print VERSION
        quit(0)
    if not os.path.isdir(path):
        print >>sys.stderr, "Not a directory: " + path
        quit(-1)
    print "Scanning: " + path
    sanitizations = sanitizeRecursively(path)
    for oldfile, newfile in sanitizations:
        print oldfile, " -> ", newfile
    print >>sys.stderr, "TEST DEBUG CLEAR DON'T INCLUDE IN RELEASE"
