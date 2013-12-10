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

import os

def get_directory_size(path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def get_directory_name(directory, default=None):
    """
      Attempts to extract a directory name given a transfer or SIP path. Expected format:
      %sharedPath%watchedDirectories/workFlowDecisions/createDip/ImagesSIP-69826e50-87a2-4370-b7bd-406fc8aad94f/

      Given this example, this function would return 'ImagesSIP'.

      If the optional `default` keyword argument is passed in, the provided value will be used if no name can be extracted.
    """
    import re

    try:
        return re.search(r'^.*/(?P<directory>.*)-[\w]{8}(-[\w]{4}){3}-[\w]{12}[/]{0,1}$', directory).group('directory')
    except:
        pass

    try:
        return re.search(r'^.*/(?P<directory>.*)/$', directory).group('directory')
    except:
        pass

    if directory:
        return directory
    else:
        return default

def get_directory_name_from_job(job):
    return get_directory_name(job.directory, default=job.sipuuid)
