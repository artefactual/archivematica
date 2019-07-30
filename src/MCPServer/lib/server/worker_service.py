from __future__ import absolute_import, unicode_literals

import logging

from django.utils import timezone
from google.protobuf.empty_pb2 import Empty

import metrics

from .protobuf_utils import current_timestamp
from .queue import job_queue
from .rpcgen import worker_pb2_grpc
from .rpcgen.worker_pb2 import Job, Task


logger = logging.getLogger("archivematica.mcp.server")


class WorkerServiceServicer(worker_pb2_grpc.WorkerServiceServicer):
    def DequeueJob(self, request, context):
        timestamp = current_timestamp()
        task_group = job_queue.get(block=True)

        logger.debug(
            "Job (uuid: %s name: %s) retrieved from queue",
            task_group.UUID,
            task_group.name(),
        )
        return Job(
            uuid=task_group.UUID,
            name=task_group.name(),
            create_time=timestamp,
            tasks=[
                Task(uuid=task.UUID, create_time=timestamp, arguments=[task.arguments])
                for task in task_group.groupTasks
            ],
        )

    def UpdateJob(self, result, context):
        future, task_group = job_queue.get_by_uuid(result.uuid)

        logger.debug(
            "Job result received (uuid: %s name: %s)", result.uuid, task_group.name()
        )

        # TODO: status checks / error handling
        for task, task_result in zip(task_group.tasks(), result.task_results):
            task_output = "\n".join(task_result.output)
            task_errors = "\n".join(task_result.errors)

            task.results.update(
                {
                    "exitCode": task_result.exit_code,
                    "stdout": task_output,
                    "stderr": task_errors,
                }
            )

            finished_timestamp = task_result.finish_time.ToDatetime()
            task.finished_timestamp = finished_timestamp
            tzinfo = timezone.get_current_timezone()
            end_time = finished_timestamp.replace(tzinfo=tzinfo)

            task_group.update_task_results(
                task_result.uuid,
                exitcode=task_result.exit_code,
                stdout=task_output,
                stderror=task_errors,
                endtime=end_time,
            )
            metrics.task_completed(task, task_group)

        future.set_result(task_group)

        return Empty()


def add_servicer(server):
    servicer = WorkerServiceServicer()
    worker_pb2_grpc.add_WorkerServiceServicer_to_server(servicer, server)
