import logging

from dbconns import auto_close_old_connections

from client.job import Job
from client import metrics


logger = logging.getLogger("archivematica.mcp.client.worker")


@auto_close_old_connections()
def run_task(task_name, job_module, jobs):
    """Do actual processing of the jobs given."""
    logger.info("\n\n*** RUNNING TASK: %s***", task_name)
    Job.bulk_set_start_times(jobs)

    try:
        job_module.call(jobs)
    except Exception as err:
        logger.exception("*** TASK FAILED: %s***", task_name)
        Job.bulk_mark_failed(jobs, str(err))
        for job in jobs:
            metrics.job_failed(task_name)
        raise
    else:
        for job in jobs:
            job.log_results()
            job.update_task_status()

            exit_code = job.get_exit_code()
            if exit_code == 0:
                metrics.job_completed(task_name)
            else:
                metrics.job_failed(task_name)
