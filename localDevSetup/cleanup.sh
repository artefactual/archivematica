#!/bin/bash

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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

if [ -e /usr/share/fits/xml/fits.xmlbackup ]; then
    sudo rm /usr/share/fits/xml/fits.xml
fi

sudo rm -r /usr/lib/archivematica
sudo rm -r /etc/archivematica
sudo rm -r /usr/share/archivematica

sudo rm /usr/bin/upload-qubit 
sudo rm /usr/bin/transcoder
sudo rm /usr/bin/archivematicaCreateMD5
sudo rm /usr/bin/archivematicaRestructureForCompliance
sudo rm /usr/bin/sanitizeNames

sudo rm -r /usr/lib/sanitizeNames

sudo rm -r /var/archivematica/

sudo rm /etc/apache2/sites-enabled/000-default
