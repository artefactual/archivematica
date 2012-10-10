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

from django.utils.dateformat import format
from main import models
import sys

# Used for raw SQL queries to return data in dictionaries instead of lists
def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

def task_duration_in_seconds(task):
    duration = int(format(task.endtime, 'U')) - int(format(task.starttime, 'U'))
    if duration == 0:
        duration = '< 1'
    return duration

def map_known_values(value):
    #changes should be made in the database, not this map
    map = {
      # currentStep
      'completedSuccessfully': 'Completed successfully',
      'completedUnsuccessfully': 'Failed',
      'exeCommand': 'Executing command(s)',
      'verificationCommand': 'Executing command(s)',
      'requiresAprroval': 'Requires approval',
      'requiresApproval': 'Requires approval',
      # jobType
      'acquireSIP': 'Acquire SIP',
      'addDCToMETS': 'Add DC to METS',
      'appraiseSIP': 'Appraise SIP',
      'assignSIPUUID': 'Asign SIP UUID',
      'assignUUID': 'Assign file UUIDs and checksums',
      'bagit': 'Bagit',
      'cleanupAIPPostBagit': 'Cleanup AIP post bagit',
      'compileMETS': 'Compile METS',
      'copyMETSToDIP': 'Copy METS to DIP',
      'createAIPChecksum': 'Create AIP checksum',
      'createDIPDirectory': 'Create DIP directory',
      'createOrMoveDC': 'Create or move DC',
      'createSIPBackup': 'Create SIP backup',
      'detoxFileNames': 'Detox filenames',
      'extractPackage': 'Extract package',
      'FITS': 'FITS',
      'normalize': 'Normalize',
      'Normalization Failed': 'Normalization failed',
      'quarantine': 'Place in quarantine',
      'reviewSIP': 'Review SIP',
      'scanForRemovedFilesPostAppraiseSIPForPreservation': 'Scan for removed files post appraise SIP for preservation',
      'scanForRemovedFilesPostAppraiseSIPForSubmission': 'Scan for removed files post appraise SIP for submission',
      'scanWithClamAV': 'Scan with ClamAV',
      'seperateDIP': 'Seperate DIP',
      'storeAIP': 'Store AIP',
      'unquarantine': 'Remove from Quarantine',
      'Upload DIP': 'Upload DIP',
      'verifyChecksum': 'Verify checksum',
      'verifyMetadataDirectoryChecksums': 'Verify metadata directory checksums',
      'verifySIPCompliance': 'Verify SIP compliance',
    }
    if value in map:
        return map[value]
    else:
        return value

def get_jobs_by_sipuuid(uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid).order_by('-createdtime')
    priorities = {
        'completedUnsuccessfully': 0,
        'requiresAprroval': 1,
        'requiresApproval': 1,
        'exeCommand': 2,
        'verificationCommand': 3,
        'completedSuccessfully': 4,
        'cleanupSuccessfulCommand': 5,
    }
    def get_priority(job):
        try: return priorities[job.currentstep]
        except Exception: return 0
    return sorted(jobs, key = get_priority) # key = lambda job: priorities[job.currentstep]
