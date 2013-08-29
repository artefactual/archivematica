#!/usr/bin/python -OO
import argparse
import tempfile
import os
import shutil
import subprocess
import sys
import time
sys.path.append('/usr/share/archivematica/dashboard')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'
from contrib.mcp.client import MCPClient
from main.models import Transfer, Job


def rsync_copy(source, destination):
    subprocess.call([
        'rsync',
        '-r',
        '-t',
        source,
        destination
    ])


def make_filepath_unique(filepath, original=None, attempt=0):
    """ Add up to 3 _ at the end of a transfer to make the name unique. """
    if original is None:
        original = filepath
    attempt = attempt + 1
    if os.path.exists(filepath):
        return make_filepath_unique(original + '_' + str(attempt), original, attempt)
    return filepath


def make_transfer(path, transfer_name):
    # url: '/filesystem/get_temp_directory/',
    temp_dir = tempfile.mkdtemp()
    transfer_dir = os.path.join(temp_dir, transfer_name)
    # url: '/filesystem/copy_transfer_component/',
    if not os.path.isdir(transfer_dir):
        os.mkdir(transfer_dir)
    # cycle through each path copying files/dirs inside it to transfer dir
    for entry in os.listdir(path):
        entry_path = os.path.join(path, entry)
        rsync_copy(entry_path, transfer_dir)

    # var url = '/filesystem/ransfer/'
    filepath = os.path.join(temp_dir, transfer_name)

    destination = os.path.join('/', 'var', 'archivematica', 'sharedDirectory', 'watchedDirectories', 'activeTransfers', 'standardTransfer', transfer_name)
    destination = make_filepath_unique(destination)
    print 'Creating transfer at', destination
    try:
        shutil.move(filepath, destination)
    except OSError:
        print 'Error copying from ' + filepath + ' to ' + destination + '. (' + str(sys.exc_info()[0]) + ')'


def approve_transfer(transfer_name):
    # Approve transfer
    approve_chain_uuid = '6953950b-c101-4f4c-a0c3-0cd0684afe5e'
    user_id = 1
    path = os.path.join('activeTransfers', 'standardTransfer', transfer_name)+'/'
    transfer = Transfer.objects.get(currentlocation__endswith=path)
    transfer_name = transfer.currentlocation.split('/')[-2]
    print 'Approving transfer UUID:', transfer_name
    job_uuid = Job.objects.get(jobtype='Approve standard transfer', sipuuid=transfer.uuid).jobuuid
    client = MCPClient()
    client.execute(job_uuid, approve_chain_uuid, user_id)


def make_transfers(num_transfers, start_number, path, transfer_name):
    names = ['{name}_{number}'.format(name=transfer_name, number=i) for i in range(start_number, start_number+num_transfers)]
    for name in names:
        make_transfer(path, name)
    print "Waiting 15 seconds for Archivematica to process transfers..."
    time.sleep(15)
    for name in names:
        approve_transfer(name)

if __name__ == '__main__':
    desc = """Create many many transfers for scalability testing.  Creates NUM_TRANSFERS transfers in Archivematica, named NAME_<number>.  <number> will start at START_NUMBER and end at START_NUMBER+NUM_TRANSFERS.
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('path', type=str, help='Path to directory to use for all the transfers')
    parser.add_argument('-n', '--num-transfers', default=1, type=int, help='Number of transfers to create')
    parser.add_argument('--start-number', default=0, type=int, help='Number to start indexing the transfers from')
    parser.add_argument('--name', type=str, default='test', help='Name of all the transfers.')
    args = parser.parse_args()
    make_transfers(args.num_transfers, args.start_number, args.path, args.name)
