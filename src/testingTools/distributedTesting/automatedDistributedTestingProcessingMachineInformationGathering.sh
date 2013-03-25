#!/bin/bash

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
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$


#-- configuration


#-- script
DATE="`date +"%Y.%m.%d-%H.%M.%S"`"

echo TODO - get archivematica revision/version
echo TODO - get ram speed and timings
echo TODO - get disk read/write speed to shared directory

sudo cat /proc/cpuinfo > ${HOSTNAME}_${DATE}_cpuinfo.log
free  > ${HOSTNAME}_${DATE}_free.log
/sbin/ifconfig|grep inet|head -1|sed 's/\:/ /'|awk '{print $3}' > ${HOSTNAME}_${DATE}_IP.log

