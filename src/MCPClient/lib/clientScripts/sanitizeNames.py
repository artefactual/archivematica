#!/usr/bin/env python2

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
