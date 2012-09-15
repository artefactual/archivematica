#!/bin/bash
#unoconvReplacementTesting1Support.sh

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


#This script is restricted, by flock in unoconvAlternative.sh, to run one at a time.
#The sleep allows for spacing between DocumentConverter.py Calls.

openOfficeNormalizationsPerformedCountFile="/tmp/OPENOFFICECOUNT"
numberOfNormalizationsBeforeRestartingOpenOfficeService=20

#create the open office count file if it doesn't exist
if [ ! -e $openOfficeNormalizationsPerformedCountFile ] ; then
	echo 0 >"$openOfficeNormalizationsPerformedCountFile"
fi

numberOfOpenOfficeNormalizations=`cat "$openOfficeNormalizationsPerformedCountFile"`

#restart the 
if [ $numberOfNormalizationsBeforeRestartingOpenOfficeService -eq $numberOfOpenOfficeNormalizations ] ;then 
	sudo /usr/lib/archivematica/transcoder/transcoderScripts/restartOpenOffice.sh
	numberOfOpenOfficeNormalizations=1
else
	numberOfOpenOfficeNormalizations=$(( $numberOfOpenOfficeNormalizations + 1 )) 
fi

echo $numberOfOpenOfficeNormalizations >$openOfficeNormalizationsPerformedCountFile

sleep 1 && "$1/DocumentConverter.py" "$2" "$3"
exit "$?"
