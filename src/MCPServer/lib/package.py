"""Package management."""

# This file is part of Archivematica.
#
# Copyright 2010-2018 Artefactual Systems Inc. <http://artefactual.com>
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

import cPickle
import collections
import logging
import os
import shutil
from tempfile import mkdtemp
from uuid import uuid4

from django.conf import settings as django_settings
import gearman

from archivematicaFunctions import unicodeToStr
from jobChain import jobChain
from main.models import Transfer, TransferMetadataSet
import storageService as storage_service
from unitTransfer import unitTransfer


logger = logging.getLogger('archivematica.mcp.server')


StartingPoint = collections.namedtuple('StartingPoint',
                                       'watched_dir chain link')

# Each package type has its corresponding watched directory and its
# associated chain, e.g. a "standard" transfer triggers the chain with UUID
# "fffd5342-2337-463f-857a-b2c8c3778c6d". This is stored in the
# WatchedDirectory model. These starting chains all have in common that they
# prompt the user to Accept/Reject the transfer.
#
# In this module we don't want to prompt the user. Instead we want to jump
# directly into action, this is whatever happens when the transfer is
# accepted. The following dictionary points to the chains and links where
# this is happening. Presumably this could be written in a generic way querying
# the workflow data but in the first iteraiton we've decided to do it this way.
# There is also the hope that the watched directories can be deprecated in the
# near future.
PACKAGE_TYPE_STARTING_POINTS = {
    'standard': StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY,
            'activeTransfers/standardTransfer'),
        chain='6953950b-c101-4f4c-a0c3-0cd0684afe5e',
        link='045c43ae-d6cf-44f7-97d6-c8a602748565',
    ),
    'unzipped bag': StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY,
            'activeTransfers/baggitDirectory'),
        chain='c75ef451-2040-4511-95ac-3baa0f019b48',
        link='154dd501-a344-45a9-97e3-b30093da35f5',
    ),
    'zipped bag': StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY,
            'activeTransfers/baggitZippedDirectory'),
        chain='167dc382-4ab1-4051-8e22-e7f1c1bf3e6f',
        link='3229e01f-adf3-4294-85f7-4acb01b3fbcf',
    ),
    'dspace': StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY,
            'activeTransfers/Dspace'),
        chain='1cb2ef0e-afe8-45b5-8d8f-a1e120f06605',
        link='bda96b35-48c7-44fc-9c9e-d7c5a05016c1',
    ),
    'maildir': StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY,
            'activeTransfers/maildir'),
        chain='d381cf76-9313-415f-98a1-55c91e4d78e0',
        link='da2d650e-8ce3-4b9a-ac97-8ca4744b019f',
    ),
    'TRIM': StartingPoint(
        watched_dir=os.path.join(
            django_settings.WATCH_DIRECTORY,
            'activeTransfers/TRIM'),
        chain='e4a59e3e-3dba-4eb5-9cf1-c1fb3ae61fa9',
        link='2483c25a-ade8-4566-a259-c6c37350d0d6',
    ),
}


def _file_is_an_archive(filepath):
    filepath = filepath.lower()
    return filepath.endswith('.zip') \
        or filepath.endswith('.tgz') \
        or filepath.endswith('.tar.gz')


def _pad_destination_filepath_if_it_already_exists(filepath, original=None,
                                                   attempt=0):
    if original is None:
        original = filepath
    attempt = attempt + 1
    if not os.path.exists(filepath):
        return filepath
    if os.path.isdir(filepath):
        return _pad_destination_filepath_if_it_already_exists(
            original + '_' + str(attempt), original, attempt)
    # need to work out basename
    basedirectory = os.path.dirname(original)
    basename = os.path.basename(original)
    # do more complex padding to preserve file extension
    period_position = basename.index('.')
    non_extension = basename[0:period_position]
    extension = basename[period_position:]
    new_basename = '{}_{}{}'.format(non_extension, attempt, extension)
    new_filepath = os.path.join(basedirectory, new_basename)
    return _pad_destination_filepath_if_it_already_exists(
        new_filepath, original, attempt)


def _check_filepath_exists(filepath):
    if filepath == '':
        return 'No filepath provided.'
    if not os.path.exists(filepath):
        return 'Filepath {} does not exist.'.format(filepath)
    if '..' in filepath:  # check for trickery
        return 'Illegal path.'
    return None


def _copy_from_transfer_sources(paths, relative_destination):
    """Copy files from source locations to the currently processing location.

    Any files in locations not associated with this pipeline will be ignored.

    :param list paths: List of paths. Each path should be formatted
                       <uuid of location>:<full path in location>
    :param str relative_destination: Path relative to the currently processing
                                     space to move the files to.
    """
    processing_location = storage_service.get_location(purpose='CP')[0]
    transfer_sources = storage_service.get_location(purpose='TS')
    files = {l['uuid']: {'location': l, 'files': []} for l in transfer_sources}

    for item in paths:
        try:
            location, path = item.split(':', 1)
        except ValueError:
            raise Exception(
                'Path {} cannot be split into location:path'.format(item))
        if location not in files:
            raise Exception('Location %(location)s is not associated'
                            ' with this pipeline' % {'location': location})

        # ``path`` will be a UTF-8 bytestring but the replacement pattern path
        # from ``files`` will be a Unicode object. Therefore, the latter must
        # be UTF-8 encoded prior. Same reasoning applies to ``destination``
        # below. This allows transfers to be started on UTF-8-encoded directory
        # names.
        source = path.replace(
            files[location]['location']['path'].encode('utf8'),
            '', 1).lstrip('/')
        # Use the last segment of the path for the destination - basename for a
        # file, or the last folder if not. Keep the trailing / for folders.
        last_segment = os.path.basename(source.rstrip('/')) + '/' \
            if source.endswith('/') else os.path.basename(source)
        destination = os.path.join(processing_location['path'].encode('utf8'),
                                   relative_destination,
                                   last_segment).replace('%sharedPath%', '')
        files[location]['files'].append({
            'source': source,
            'destination': destination
        })
        logger.debug('source: %s, destination: %s', source, destination)

    message = []
    for item in files.values():
        reply, error = storage_service.copy_files(
            item['location'], processing_location, item['files'])
        if reply is None:
            message.append(str(error))
    if message:
        raise Exception('The following errors occured: %(message)s'
                        % {'message': ', '.join(message)})


def _move_to_internal_shared_dir(filepath, dest, transfer):
    """Move package to an internal Archivematica directory.

    The side effect of this function is to update the transfer object with the
    final location. This is important so other components can continue the
    processing. When relying on watched directories to start a transfer (see
    _start_package_transfer), this also matters because unitTransfer is going
    to look up the object in the database based on the location.
    """
    error = _check_filepath_exists(filepath)
    if error:
        raise Exception(error)
    # Confine destination to subdir of originals.
    basename = os.path.basename(filepath)
    dest = _pad_destination_filepath_if_it_already_exists(
        os.path.join(dest, basename))
    # Ensure directories end with a trailing slash.
    if os.path.isdir(filepath):
        dest = os.path.join(dest, '')
    try:
        shutil.move(filepath, dest)
    except (OSError, shutil.Error) as e:
        raise Exception('Error moving from %s to %s (%s)', filepath, dest, e)
    else:
        transfer.currentlocation = dest.replace(
            django_settings.SHARED_DIRECTORY, '%sharedPath%', 1)
        transfer.save()


def create_package(name, type_, accession, path, metadata_set_id,
                   auto_approve=True):
    """Create new package.

    It creates the Transfer object and submits the job to the intenral queue.
    """
    if not name:
        raise ValueError('No transfer name provided.')
    if not path:
        raise ValueError('No path provided.')
    name = unicodeToStr(name)
    if type_ is None or type_ == 'disk image':
        type_ = 'standard'
    if type_ not in PACKAGE_TYPE_STARTING_POINTS:
        raise ValueError('Unexpected type of package provided')
    # Create Transfer object.
    kwargs = {'uuid': str(uuid4())}
    if accession is not None:
        kwargs['accessionid'] = unicodeToStr(accession)
    if metadata_set_id is not None:
        try:
            kwargs['transfermetadatasetrow'] = \
                TransferMetadataSet.objects.get(id=metadata_set_id)
        except TransferMetadataSet.DoesNotExist:
            pass
    transfer = Transfer.objects.create(**kwargs)
    logger.debug('Transfer object created: %s', transfer.pk)
    _submit_create_package_internal_job(transfer.pk, name, type_, path,
                                        auto_approve)
    return transfer


def _submit_create_package_internal_job(id_, name, type_, path,
                                        auto_approve=True):
    """Submit package creation background job to queue."""
    payload = {
        'id': id_, 'name': name, 'type': type_, 'path': path,
        'auto_approve': auto_approve,
    }
    gm_client = gearman.GearmanClient([django_settings.GEARMAN_SERVER])
    logger.debug('Submitting job MCPServerInternalPackageStartTransfer (%s)',
                 payload)
    response = gm_client.submit_job('MCPServerInternalPackageStartTransfer',
                                    cPickle.dumps(payload),
                                    background=True,
                                    wait_until_complete=False)
    gm_client.shutdown()
    return response


def _capture_transfer_failure(fn):
    """Detect errors during transfer/ingest."""
    def wrap(*args, **kwargs):
        try:
            # Our decorated function isn't expected to return anything.
            fn(*args, **kwargs)
        except Exception as err:
            # The main purpose of this decorator is to update the Transfer with
            # the new state (fail). If the Transfer does not exist we give up.
            if isinstance(err, Transfer.DoesNotExist):
                raise
        else:
            # No exceptions!
            return
        # At this point we know that the transfer has failed and we want to do
        # our best effort to update the state without further interruptions.
        try:
            Transfer.objects.get(pk=args[0])
            #
            # TODO: update state once we have a FSM.
            #
        except Exception:
            pass
        # Finally raised the exception and log it.
        try:
            logger.exception('Exception: %s', err, exc_info=True)
        except NameError:
            pass
    return wrap


def _determine_transfer_paths(name, path, tmpdir):
    if _file_is_an_archive(path):
        transfer_dir = tmpdir
        p = path.split(':', 1)[1]
        filepath = os.path.join(tmpdir, os.path.basename(p))
    else:
        path = os.path.join(path, '.')  # Copy contents of dir but not dir
        transfer_dir = filepath = os.path.join(tmpdir, name)
    return (
        transfer_dir.replace(django_settings.SHARED_DIRECTORY, '', 1),
        unicodeToStr(filepath),
        path
    )


@_capture_transfer_failure
def _start_package_transfer_with_auto_approval(id_, name, path,
                                               tmpdir, starting_point,
                                               transfer):
    """Start transfer manually.

    This method does not rely on the activeTransfer watched directory. It
    blocks until the process completes.
    """
    transfer_rel, filepath, path = _determine_transfer_paths(name, path, tmpdir)
    logger.debug('Package %s: determined vars '
                 'transfer_rel=%s, filepath=%s, path=%s',
                 id_, transfer_rel, filepath, path)

    logger.debug('Package %s: copying chosen contents from transfer sources'
                 ' (from=%s, to=%s)', id_, path, transfer_rel)
    _copy_from_transfer_sources([path], transfer_rel)

    logger.debug('Package %s: moving package to processing directory', id_)
    _move_to_internal_shared_dir(
        filepath, django_settings.PROCESSING_DIRECTORY, transfer)

    logger.debug('Package %s: starting workflow processing', id_)
    unit = unitTransfer(path, id_)
    jobChain(unit, starting_point.chain, starting_point.link)


@_capture_transfer_failure
def _start_package_transfer(id_, name, path, tmpdir, starting_point, transfer):
    """Start a new transfer by moving it to the corresponding watched dir."""
    transfer_rel, filepath, path = _determine_transfer_paths(name, path, tmpdir)
    logger.debug('Package %s: determined vars '
                 'transfer_rel=%s, filepath=%s, path=%s',
                 id_, transfer_rel, filepath, path)

    logger.debug('Package %s: copying chosen contents from transfer sources '
                 '(from=%s, to=%s)', id_, path, transfer_rel)
    _copy_from_transfer_sources([path], transfer_rel)

    logger.debug('Package %s: moving package to activeTransfers dir '
                 'from=%s, to=%s)', id_, filepath, starting_point.watched_dir)
    # MCPServer will pick up the transfer when once moved into the watched dir.
    _move_to_internal_shared_dir(filepath, starting_point.watched_dir, transfer)


def start_package_transfer(id_, name, type_, path, auto_approve):
    """Start package transfer.

    The auto approval keyword determines the underlyng function that we're
    going to use. Their implementations are significantly different.

    TODO: use tempfile.TemporaryDirectory as a context manager once we move to
    Python 3.
    """
    tmpdir = mkdtemp(dir=os.path.join(django_settings.SHARED_DIRECTORY, 'tmp'))
    transfer = Transfer.objects.get(pk=id_)
    logger.debug('Package %s: starting transfer (%s)',
                 id_, (name, type_, path, tmpdir))
    try:
        sp = PACKAGE_TYPE_STARTING_POINTS.get(type_)
        if auto_approve is True:
            _start_package_transfer_with_auto_approval(id_, name, path,
                                                       tmpdir, sp,
                                                       transfer)
            return
        elif auto_approve is False:
            _start_package_transfer(id_, name, path, tmpdir, sp, transfer)
        else:
            raise ValueError('Unexpected value in auto_approve parameter')
    finally:
        os.chmod(tmpdir, 0o770)  # Needs to be writeable by the SS.
        return tmpdir
