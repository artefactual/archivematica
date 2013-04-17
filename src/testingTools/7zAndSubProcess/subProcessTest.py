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
# @subpackage testing
# @author Joseph Perry <joseph@artefactual.com>


import sys
import os
import shlex
import subprocess

#unicode fix
fix = True

def extract(i):
    my_env = os.environ
    if fix:
        my_env['PYTHONIOENCODING'] = 'utf-8'
    stdIn = None
    command = """7z a -bd -t7z -y -m0=lzma -mx=5 -mta=on -mtc=on -mtm=on "testnow%d.7z" ./BagTransfer""" % i
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=my_env)
    stdOut, stdError = p.communicate(input=stdIn)
    print stdOut
    print >>sys.stderr, stdError


if __name__ == '__main__':
    print sys.stdout.encoding
    print __file__
    print u'\u2019'.encode('utf-8'),
    print u'\u2019'
    i = 0
    if len(sys.argv) != 2:
        i = 0
    else:
        i = int(sys.argv[1]) + 1
    command = "%s %d" % (__file__, i)
    print i
    extract(i)
    if i < 3:
        my_env = os.environ
        if fix:
            my_env['PYTHONIOENCODING'] = 'utf-8'
        #for key, value in my_env.iteritems():
        #    print key, ":\t", value
        stdIn = None
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=my_env)
        stdOut, stdError = p.communicate(input=stdIn)
        print stdOut
        print >>sys.stderr, stdError 
    