import functools
import logging
import multiprocessing
import pickle

import gearman
from client import metrics
from client.job import Job
from client.loader import load_job_modules
from client.utils import parse_command_line
from client.utils import replace_task_arguments
from client.worker import run_task
from django.conf import settings


logger = logging.getLogger("archivematica.mcp.client.gearman")


class PickleDataEncoder(gearman.DataEncoder):
    @classmethod
    def encode(cls, encodable_object):
        return pickle.dumps(encodable_object, protocol=0)

    @classmethod
    def decode(cls, decodable_bytes):
        return pickle.loads(decodable_bytes)


class MCPGearmanWorker(gearman.GearmanWorker):
    data_encoder = PickleDataEncoder

    def __init__(
        self, hosts, client_scripts, shutdown_event=None, max_jobs_to_process=None
    ):
        super().__init__(hosts)

        self.job_modules = load_job_modules(settings.CLIENT_MODULES_FILE)
        self.client_id = f"MCPClient-{multiprocessing.current_process().pid}"
        self.jobs_processed_count = 0
        self.max_jobs_to_process = max_jobs_to_process
        self.shutdown_event = shutdown_event

        self.set_client_id(self.client_id.encode("ascii"))

        for client_script in client_scripts:
            task_handler = functools.partial(self.handle_job, client_script)
            self.register_task(client_script.encode(), task_handler)

        logger.debug("Worker %s registered tasks: %s", self.client_id, client_scripts)

    @staticmethod
    def _format_job_results(jobs):
        results = {}

        for job in jobs:
            results[job.uuid] = {
                "exitCode": job.get_exit_code(),
                "finishedTimestamp": job.end_time,
            }

            if job.capture_output:
                # Send back stdout/stderr so it can be written to files.
                # Most cases don't require this (logging to the database is
                # enough), but the ones that do are coordinated through the
                # MCP Server so that multiple MCP Client instances don't try
                # to write the same file at the same time.
                results[job.uuid]["stdout"] = job.get_stdout()
                results[job.uuid]["stderror"] = job.get_stderr()

        return results

    @staticmethod
    def _prepare_jobs(task_name, gearman_job):
        """Given a tasks dictionary, return a list of Job objects."""
        tasks = gearman_job.data["tasks"]

        jobs = []
        for task_uuid, task_data in tasks.items():
            arguments = str(task_data["arguments"])
            arguments = replace_task_arguments(
                arguments, task_uuid, task_data.get("createdDate")
            )
            arguments = parse_command_line(arguments)

            wants_output = task_data.get("wants_output", True)

            job = Job(task_name, task_uuid, arguments, capture_output=wants_output)
            jobs.append(job)

        return jobs

    def handle_job(self, task_name, gearman_worker, gearman_job):
        task_name = str(task_name)
        job_module = self.job_modules[task_name]
        logger.debug(
            "Gearman job request %s received for %s", gearman_job.unique, task_name
        )

        with metrics.task_execution_time_histogram.labels(script_name=task_name).time():
            jobs = self._prepare_jobs(task_name, gearman_job)
            # run task will update jobs in place, by reference
            run_task(task_name, job_module, jobs)

            self.jobs_processed_count += 1

            return {"task_results": self._format_job_results(jobs)}

    def on_job_exception(self, current_job, exc_info):
        logger.error(
            "An unhandled exception occurred processing a Gearman job",
            exc_info=exc_info,
        )
        return super().on_job_exception(current_job, exc_info)

    def after_poll(self, any_activity):
        """Hook for worker exit after a poll.

        We exit if the shutdown event has been set, or if `max_jobs_to_process`
        jobs have been completed.
        """
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Gearman Worker exited due to shutdown")
            return False

        if (
            self.max_jobs_to_process is not None
            and self.jobs_processed_count >= self.max_jobs_to_process
        ):
            logger.debug(
                "Worker exiting work loop after processing %s jobs",
                self.jobs_processed_count,
            )
            return False

        return True
