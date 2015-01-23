#!/usr/bin/python -OO

import logging
import os
import shutil
import sys

# archivematicaCommon
import storageService as storage_service

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log",
    level=logging.INFO)


def main(transfer_uuid, transfer_path):
    current_location = storage_service.get_location(purpose="CP")[0]
    backlog = storage_service.get_location(purpose="BL")[0]

    # Get size recursively for Transfer
    size = 0
    for dirpath, _, filenames in os.walk(transfer_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            size += os.path.getsize(file_path)

    # Make Transfer path relative to Location
    shared_path = os.path.join(current_location['path'], '')
    relative_transfer_path = transfer_path.replace(shared_path, '')

    # TODO this should use the same value as
    # dashboard/src/components/filesystem_ajax/views.py DEFAULT_BACKLOG_PATH
    transfer_name = os.path.basename(transfer_path.rstrip('/'))
    backlog_path = os.path.join('originals', transfer_name)

    (new_file, error_msg) = storage_service.create_file(
        uuid=transfer_uuid,
        origin_location=current_location['resource_uri'],
        origin_path=relative_transfer_path,
        current_location=backlog['resource_uri'],
        current_path=backlog_path,
        package_type='transfer',  # TODO use constant from storage service
        size=size,
    )
    if new_file is not None and new_file.get('status', '') != "FAIL":
        message = "Transfer moved to backlog: {}".format(new_file)
        logging.info(message)
        print message
        # TODO update transfer location?  Files location?

        # Delete transfer from processing space
        shutil.rmtree(transfer_path)
        return 0
    else:
        print >>sys.stderr, "Moving to backlog failed.  See Storage Service logs for more details"
        print >>sys.stderr, error_msg or "Package status: Failed"
        logging.warning("Moving to backlog failed: {}.  See logs for more details.".format(error_msg))
        return 1


if __name__ == '__main__':
    transfer_uuid = sys.argv[1]
    transfer_path = sys.argv[2]
    sys.exit(main(transfer_uuid, transfer_path))
