from __future__ import absolute_import, division, print_function, unicode_literals

import logging


from django.conf import settings

from client import loader
from client.job import Job


logger = logging.getLogger("archivematica.mcp.client.worker")
job_modules = loader.load_job_modules(settings.CLIENT_MODULES_FILE)


def run_task(task_name, jobs):
    """Do actual processing of the jobs given.
    """
    logger.info("\n\n*** RUNNING TASK: %s***", task_name)
    Job.bulk_set_start_times(jobs)

    client_script = job_modules[task_name]
    try:
        client_script.call(jobs)
    except Exception as err:
        logger.exception("*** TASK FAILED: %s***", task_name)
        Job.bulk_mark_failed(jobs, err.message)
        raise
    else:
        for job in jobs:
            job.log_results()
            job.update_task_status()
