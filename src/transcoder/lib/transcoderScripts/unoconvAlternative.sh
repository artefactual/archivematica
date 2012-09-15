#!/bin/bash

# This file is part of Archivematica.
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
# @subpackage Transcoder
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

#%accessFormat% %fileFullName% %preservationFileDirectory%%fileTitle%.%accessFormat% %accessFileDirectory%
#"%fileFullName%" "%outputDirectory%%prefix%%fileName%%postfix%.tif"

outputExtension="PDF"
ddirname="`dirname %fileFullName%`"
dbasename="`basename %fileFullName%`"  
cd "$ddirname"
outputFile="%fileDirectory%%prefix%%fileName%%postfix%.${outputExtension}"

flock -x /var/lock/documentConversion.lock -c "\"/usr/lib/transcoder/transcoderScripts/unoconvAlternativeSupport.sh\" \"/usr/lib/transcoder/transcoderScripts\" \"${dbasename}\" \"${outputFile}\"" && mv "${outputFile}" "%outputDirectory%"
exit "$?"
