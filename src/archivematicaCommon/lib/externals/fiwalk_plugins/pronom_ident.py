#!/usr/bin/env python
# encoding: utf-8
"""
pronom-ident.py - Identify a bitstream against PRONOM; uses fido
"""
from __future__ import print_function

# https://github.com/anarchivist/fiwalk-dgi/blob/master/python/pronom_ident.py
# Author  anarchivist
from __future__ import absolute_import

import os
import sys
import time
from optparse import OptionParser
from fido import fido


class FiwalkFido(fido.Fido):
    """docstring for FiwalkFido"""

    def __init__(self, **kwargs):
        fido.Fido.__init__(self, kwargs)
        self.handle_matches = self.parse_matches

    def identify_file(self, filename):
        """Identify the type of @param filename."""
        self.current_file = filename
        try:
            t0 = time.clock()
            f = open(filename, "rb")
            size = os.stat(filename)[6]
            self.current_filesize = size
            bofbuffer, eofbuffer, __ = self.get_buffers(f, size, seekable=True)
            matches = self.match_formats(bofbuffer, eofbuffer)
            # from here is also repeated in walk_zip
            # we should make this uniform in next version!
            #
            # filesize is made conditional because files with 0 bytes
            # are falsely characterised being 'rtf'
            # in these cases we try to match the extension instead
            if len(matches) > 0 and self.current_filesize > 0:
                return self.handle_matches(
                    filename, matches, time.clock() - t0, "signature"
                )
            elif len(matches) == 0 or self.current_filesize == 0:
                matches = self.match_extensions(filename)
                return self.handle_matches(
                    filename, matches, time.clock() - t0, "extension"
                )
            # till here matey!
            if self.zip:
                self.identify_contents(filename, type=self.container_type(matches))
        except IOError:
            # print >> sys.stderr, "FIDO: Error in identify_file: Path is {0}".format(filename)
            sys.stderr.write(
                "FIDO: Error in identify_file: Path is {0}\n".format(filename)
            )

    def parse_matches(self, fullname, matches, delta_t, matchtype=""):
        out = {}
        out["pronomSoftware"] = "fido " + fido.version
        out["pronomTotalMatches"] = len(matches)
        if len(matches) == 0:
            out["pronomMatchType"] = "fail"
        else:
            i = 0
            for (f, s) in matches:
                i += 1
                out["pronomMatchType"] = matchtype
                out["pronomPuid"] = self.get_puid(f)
                out["pronomFormatName"] = f.find("name").text
                out["pronomSignatureName"] = s.find("name").text
                mime = f.find("mime")
                out["pronomFormatMimeType"] = mime.text if mime is not None else None
                version = f.find("version")
                out["pronomFormatVersion"] = (
                    version.text if version is not None else None
                )
                alias = f.find("alias")
                out["pronomFormatAlias"] = alias.text if alias is not None else None
        return out


def pronom_ident(fn):
    f = FiwalkFido(quiet=True)
    return f.identify_file(fn)


def main():
    parser = OptionParser()
    opts, args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        exit(-1)

    filename = args[0]
    out = pronom_ident(filename)

    for k, v in out.items():
        if v is not None:
            print(k + ": " + str(v))


if __name__ == "__main__":
    sys.exit(main())
