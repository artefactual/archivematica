""" ... """

from socket import gethostname
import logging
import time

from django.conf import settings as django_settings
import gearman

from worker_util import log_exceptions, unpickle_payload, pickle_result
from package import start_package_transfer


LOGGER = logging.getLogger("archivematica.mcp.server.worker")


@pickle_result
@unpickle_payload
@log_exceptions(LOGGER)
def package_start_transfer_handler(*args, **kwargs):
    payload = kwargs['payload']
    start_package_transfer(
        payload.get('id'),
        payload.get('name'),
        payload.get('type'),
        payload.get('path'),
        payload.get('auto_approve', True),
    )


def start_worker(name):
    client_id = '{}_{}_MCPServer_worker'.format(gethostname(), name)
    gm_worker = gearman.GearmanWorker([django_settings.GEARMAN_SERVER])
    gm_worker.set_client_id(client_id)
    gm_worker.register_task(
        'MCPServerInternalPackageStartTransfer',
        package_start_transfer_handler)
    LOGGER.debug('Created new MCPserver worker (id=%s)', client_id)

    fail_max_sleep = 30
    fail_sleep = 1
    fail_sleep_inc = 2
    while True:
        try:
            gm_worker.work()
        except gearman.errors.ServerUnavailable:
            time.sleep(fail_sleep)
            if fail_sleep < fail_max_sleep:
                fail_sleep += fail_sleep_inc
