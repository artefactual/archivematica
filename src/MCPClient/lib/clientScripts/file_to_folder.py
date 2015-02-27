#!/usr/bin/env python

from __future__ import print_function
import os
import sys

# dashboard
from main.models import Transfer

def main(transfer_path, transfer_uuid, shared_path):
    """
    Move a Transfer that is a file into a directory.

    Given a transfer that is one file, move the file into a directory with the same basename and updated the DB for the new path.
    No action taken if the transfer is already a directory.

    WARNING This should not be run inside a watched directory - may result in duplicated transfers.

    :param transfer_path: Path to the current transfer, file or folder
    :param transfer_uuid: UUID of the transfer to update
    :param shared_path: Value of the %sharedPath% variable
    """
    # If directory, return unchanged
    if os.path.isdir(transfer_path):
        print(transfer_path, 'is a folder, no action needed. Exiting.')
        return 0
    # If file, move into directory and update transfer
    dirpath = os.path.splitext(transfer_path)[0]
    basename = os.path.basename(transfer_path)
    if os.path.exists(dirpath):
        print('Cannot move file', transfer_path, 'to folder', dirpath, 'because it already exists', file=sys.stderr)
        return 1
    os.mkdir(dirpath)
    new_path = os.path.join(dirpath, basename)
    print('Moving', transfer_path, 'to', new_path)
    os.rename(transfer_path, new_path)

    db_path = os.path.join(dirpath.replace(shared_path, '%sharedPath%', 1), '')
    print('Updating transfer', transfer_uuid, 'path to', db_path)
    Transfer.objects.filter(uuid=transfer_uuid).update(currentlocation=db_path)
    return 0

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    transfer_uuid = sys.argv[2]
    shared_path = sys.argv[3]
    sys.exit(main(transfer_path, transfer_uuid, shared_path))
