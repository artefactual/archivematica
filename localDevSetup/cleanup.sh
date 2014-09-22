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
# @author Justin Simpson <jsimpson@artefactual.com>

# this loop is required because we need to leave storage service files alone
dirs=("/usr/lib/archivematica" "/etc/archivematica" "/usr/share/archivematica" "/var/archivematica")
for dir in ${dirs[@]} 
do
    if [ "$(ls -A $dir)" ]; then
        find $dir -type l | while read file ; do
            if [[ ! ${file} =~ "storage" ]]; then
                sudo rm ${file}
            fi
        done
        if  [ ! "$(ls -A $dir)" ]; then
            sudo rmdir $dir 
        fi
    fi
done

sudo rm /etc/apache2/sites-enabled/000-default.conf
