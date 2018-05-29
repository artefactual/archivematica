"""Provide functionality to set up workers and run Archivematica commands."""

import cPickle
import logging
from socket import gethostname
import traceback

from django.conf import settings as django_settings
import gearman

from main.models import Task
from databaseFunctions import auto_close_db, getUTCDate as get_utc_date
from executeOrRunSubProcess import executeOrRun as execute_or_run

from modules import supported_modules


logger = logging.getLogger('archivematica.mcp.client')


replacement_dict = {
    "%sharedPath%": django_settings.SHARED_DIRECTORY,
    "%clientScriptsDirectory%": django_settings.CLIENT_SCRIPTS_DIRECTORY,
    "%clientAssetsDirectory%": django_settings.CLIENT_ASSETS_DIRECTORY,
}


class ProcessGearmanJobError(Exception):
    """ProcessGearmanJobError is an error occurred while executing a command."""

    def pickle(self):
        """Serialize error."""
        return _serialize_job_response(**self.args)


def _execute_command(gearman_job, gearman_worker):
    """Execute MCPClient supported module or command.

    Process a Gearman job/task: return a 2-tuple consisting of a script
    string (a command-line script with arguments) and a task UUID string. Raise
    a custom exception if the client script is unregistered or if the task has
    already been started.
    """
    # ``client_script`` is a string matching one of the keys (i.e., client
    # scripts) in the global ``supported_modules`` dict.
    client_script = gearman_job.task
    task_uuid = str(gearman_job.unique)
    logger.info('Executing %s (%s)', client_script, task_uuid)
    data = cPickle.loads(gearman_job.data)
    utc_date = get_utc_date()
    arguments = data['arguments']
    if isinstance(arguments, unicode):
        arguments = arguments.encode('utf-8')
    client_id = gearman_worker.worker_client_id
    task = Task.objects.get(taskuuid=task_uuid)
    if task.starttime is not None:
        raise ProcessGearmanJobError({
            'exit_code': -1,
            'stdout': '',
            'stderr': 'Detected this task has already started!\n'
                      'Unable to determine if it completed successfully.'})
    task.client = client_id
    task.starttime = utc_date
    task.save()
    client_script_full_path = supported_modules.get(client_script)
    if not client_script_full_path:
        raise ProcessGearmanJobError({
            'exit_code': -1,
            'stdout': 'Error!',
            'stderr': 'Error! - Tried to run an unsupported command.'})
    replacement_dict['%date%'] = utc_date.isoformat()
    replacement_dict['%jobCreatedDate%'] = data['createdDate']
    # Replace replacement strings
    for var, val in replacement_dict.items():
        # TODO: this seems unneeded because the full path to the client
        # script can never contain '%date%' or '%jobCreatedDate%' and the
        # other possible vars have already been replaced.
        client_script_full_path = client_script_full_path.replace(var, val)
        arguments = arguments.replace(var, val)
    arguments = arguments.replace('%taskUUID%', task_uuid)
    script = client_script_full_path + ' ' + arguments
    return script, task_uuid


def _unexpected_error():
    logger.exception('Unexpected error')
    return _serialize_job_response(-1, '', traceback.format_exc())


def _serialize_job_response(exit_code, stdout, stderr):
    """Serialize job response.

    Do not change this unless MCPServer is updated accordingly!
    """
    return cPickle.dumps({'exitCode': exit_code,
                          'stdOut': stdout,
                          'stdError': stderr})


@auto_close_db
def process_gearman_job(gearman_worker, gearman_job):
    """Run a job requested by Gearman.

    This function is executed by GearmanWorker when a job is assigned to this
    worker. It executes the command encoded in ``gearman_job`` and returns its
    exit code, standard output and standard error as a pickled dict.
    """
    try:
        script, task_uuid = _execute_command(
            gearman_job, gearman_worker)
    except ProcessGearmanJobError as error:
        return error.pickle()
    except Exception:
        return _unexpected_error()
    logger.info('<processingCommand>{%s}%s</processingCommand>',
                task_uuid, script)
    try:
        exit_code, std_out, std_error = execute_or_run(
            'command', script, stdIn='', printing=True)
    except OSError:
        logger.exception('Execution failed')
        return _serialize_job_response(1, 'Archivematica Client Error!',
                                       traceback.format_exc())
    except Exception:
        return _unexpected_error()
    return _serialize_job_response(exit_code, std_out, std_error)


def get_worker(gearman_servers, name=None):
    """Set up Gearman worker object."""
    worker = gearman.GearmanWorker(gearman_servers)

    # This sets the worker ID in a job server so monitoring and reporting
    # commands can uniquely identify the various workers, and different
    # connections to job servers from the same worker.
    client_id = gethostname()
    if name is not None:
        client_id = '{}_{}'.format(client_id, name)
    worker.set_client_id(gethostname())

    # Notify the Gearman server that this worker is available to perform the
    # functions that we've encoded in `supported_modules`. The worker will be
    # put on a list to be woken up whenever the job server receives a job for
    # these functions (modules).
    for client_script in supported_modules:
        logger.info('Registering module %s in worker %s.',
                    client_script, client_id)
        worker.register_task(client_script, process_gearman_job)

    return worker
