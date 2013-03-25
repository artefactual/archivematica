#!/bin/bash
#
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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

#create temp report files
UUID=`uuid`
failTmp=/tmp/fail-$UUID
passTmp=/tmp/pass-$UUID
reportTmp=/tmp/report-$UUID

checkFolder="$1"
md5Digest="$2"
integrityReport="$3"
checksumTool="$4"

tmpDir=`pwd`
cd "$checkFolder"
#check for passing checksums
"${checksumTool}" -r -m "$md5Digest" . > $passTmp
#check for failing checksums
"${checksumTool}" -r -n -m "$md5Digest" . > $failTmp
cd $tmpDir      



#Count number of Passed/Failed
numberPass=`wc -l $passTmp| cut -d" " -f1`
numberFail=`wc -l $failTmp| cut -d" " -f1`

#Create report
echo "PASSED" >> $reportTmp
cat $passTmp >> $reportTmp
echo " " >> $reportTmp
echo $numberPass "items passed integrity checking" >> $reportTmp
echo " " >> $reportTmp
echo " " >> $reportTmp
echo "FAILED" >> $reportTmp
cat $failTmp >> $reportTmp
echo " " >> $reportTmp
echo $numberFail "items failed integrity checking" >> $reportTmp

#copy pasta
cp $reportTmp "$integrityReport"
cat $failTmp 1>&2

#cleanup
rm $failTmp $passTmp $reportTmp

exit $numberFail
