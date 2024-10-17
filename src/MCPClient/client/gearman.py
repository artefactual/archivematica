import functools
import logging
import multiprocessing
from datetime import datetime
from multiprocessing.synchronize import Event
from types import TracebackType
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

import gearman
from django.conf import settings
from gearman.job import GearmanJob
from gearman_encoder import JSONDataEncoder

from client import metrics
from client.job import Job
from client.loader import load_job_modules
from client.utils import parse_command_line
from client.utils import replace_task_arguments
from client.worker import run_task

# This is how `gearman_job.data["tasks"]` looks in the `_prepare_jobs`` method
# below:
# {
#     "8022802f-6097-43d8-b217-2ed7f2b38f09": {
#         "arguments": '"c6e07b1d-8b42-46e4-9ad5-53e7e6ae6d59" ' '"Standard"',
#         "createdDate": "2024-08-04T21:34:35.241750+00:00",
#         "uuid": "8022802f-6097-43d8-b217-2ed7f2b38f09",
#         "wants_output": False,
#     },
#     ...
# }
TaskData = Dict[str, Union[str, bool]]
GearmanJobTasks = Dict[str, TaskData]

# This is how `results` looks in the `_format_job_results` method below:
# {
#     "3e0a1962-bd4b-4b04-8d2a-ba273e65fe7f": {
#         "exitCode": 0,
#         "finishedTimestamp": datetime.datetime(
#             2024, 8, 4, 21, 44, 55, 661575, tzinfo=datetime.timezone.utc
#         ),
#         "stderror": "",
#         "stdout": "",
#     },
#     ...
# }
JobData = Dict[str, Union[int, Optional[datetime], str]]
JobResults = Dict[str, JobData]

logger = logging.getLogger("archivematica.mcp.client.gearman")


class MCPGearmanWorker(gearman.GearmanWorker):  # type: ignore
    data_encoder = JSONDataEncoder

    def __init__(
        self,
        hosts: List[str],
        client_scripts: List[str],
        shutdown_event: Optional[Event] = None,
        max_jobs_to_process: Optional[int] = None,
    ) -> None:
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
    def _format_job_results(jobs: List[Job]) -> JobResults:
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
    def _prepare_jobs(task_name: str, gearman_job: GearmanJob) -> List[Job]:
        """Given a tasks dictionary, return a list of Job objects."""
        tasks: GearmanJobTasks = gearman_job.data["tasks"]

        jobs = []
        for task_uuid, task_data in tasks.items():
            # We use ISO 8601 in our wire format but replace the `T` separator
            # with a space for METS compatibility in client scripts.
            created_date = datetime.fromisoformat(
                str(task_data["createdDate"])
            ).isoformat(" ")
            arguments = replace_task_arguments(
                str(task_data["arguments"]),
                task_uuid,
                created_date,
            )
            arguments = parse_command_line(arguments)
            wants_output = task_data.get("wants_output", True)

            job = Job(task_name, task_uuid, arguments, capture_output=wants_output)
            jobs.append(job)

        return jobs

    def handle_job(
        self,
        task_name: str,
        gearman_worker: gearman.GearmanWorker,
        gearman_job: GearmanJob,
    ) -> Dict[str, JobResults]:
        job_module = self.job_modules[task_name]
        logger.debug(
            "Gearman job request %s received for %s",
            gearman_job.unique.decode(),
            task_name,
        )

        with metrics.task_execution_time_histogram.labels(script_name=task_name).time():
            jobs = self._prepare_jobs(task_name, gearman_job)
            # run task will update jobs in place, by reference
            run_task(task_name, job_module, jobs)

            self.jobs_processed_count += 1

            return {"task_results": self._format_job_results(jobs)}

    def on_job_exception(
        self,
        current_job: GearmanJob,
        exc_info: Tuple[Type[BaseException], BaseException, TracebackType],
    ) -> bool:
        logger.error(
            "An unhandled exception occurred processing a Gearman job",
            exc_info=exc_info,
        )
        # Casting to bool until GearmanWorker gets type annotations.
        return bool(super().on_job_exception(current_job, exc_info))

    def after_poll(self, any_activity: bool) -> bool:
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
