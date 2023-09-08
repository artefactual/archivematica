"""
A Job is MCPClient's representation of a unit of work to be
performed--corresponding to a Task on the MCPServer side.  Jobs are run in
batches by clientScript modules and populated with an exit code, standard out
and standard error information.
"""
import logging
import sys
import traceback
from contextlib import contextmanager

from django.conf import settings
from django.utils import timezone
from main.models import Task


logger = logging.getLogger("archivematica.mcp.client.job")


class Job:
    def __init__(self, name, uuid, arguments, capture_output=False):
        """
        Arguments:
            name: job type, e.g. `move_sip`.
            uuid: Unique id for this job
            arguments: list of command line argument strings, e.g ["param1", "--foo"]
        Keyword arguments:
            capture_output: Flag for determining if output should be sent back to MCPServer
        """
        self.name = name
        self.uuid = uuid
        self.args = [name] + arguments
        self.capture_output = capture_output
        self.int_code = 0
        self.status_code = ""
        self.output = ""
        self.error = ""

        self.start_time = None
        self.end_time = None

    @classmethod
    def bulk_set_start_times(cls, jobs):
        """Bulk set the processing start time for a batch of jobs."""
        start_time = timezone.now()
        uuids = [job.uuid for job in jobs]
        Task.objects.filter(taskuuid__in=uuids).update(starttime=start_time)
        for job in jobs:
            job.start_time = start_time

    @classmethod
    def bulk_mark_failed(cls, jobs, message):
        uuids = [job.uuid for job in jobs]

        Task.objects.filter(taskuuid__in=uuids).update(
            stderror=str(message), exitcode=1, endtime=timezone.now()
        )
        for job in jobs:
            job.set_status(1, status_code=message)

    def log_results(self):
        logger.info(
            (
                "#<%s; exit=%s; code=%s uuid=%s\n"
                "=============== STDOUT ===============\n"
                "%s"
                "\n=============== END STDOUT ===============\n"
                "=============== STDERR ===============\n"
                "%s"
                "\n=============== END STDERR ===============\n"
                "\n>"
            ),
            self.name,
            self.get_exit_code(),
            self.status_code,
            self.uuid,
            self.get_stdout(),
            self.get_stderr(),
        )

    def update_task_status(self):
        """Updates the Task model after a job has been completed."""
        # Not all jobs set an exit code. They expect a default of 0,
        # so keep compatibility with that
        if self.int_code is None:
            self.set_status(0)
        self.end_time = timezone.now()

        kwargs = {"exitcode": self.get_exit_code(), "endtime": self.end_time}
        if settings.CAPTURE_CLIENT_SCRIPT_OUTPUT:
            kwargs.update({"stdout": self.get_stdout(), "stderror": self.get_stderr()})
        Task.objects.filter(taskuuid=self.uuid).update(**kwargs)

    def set_status(self, int_code, status_code="success"):
        if int_code:
            self.int_code = int(int_code)
        self.status_code = status_code

    def write_output(self, s):
        self.output += s

    def write_error(self, s):
        self.error += s

    def print_output(self, *args):
        self.write_output(" ".join([str(x) for x in args]) + "\n")

    def print_error(self, *args):
        self.write_error(" ".join([str(x) for x in args]) + "\n")

    def pyprint(self, *objects, **kwargs):
        output_type = kwargs.get("file", sys.stdout)
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        msg = sep.join([str(x) for x in objects]) + end

        if output_type is sys.stdout:
            self.write_output(msg)
        elif output_type is sys.stderr:
            self.write_error(msg)
        else:
            raise Exception("Unrecognised print file: " + str(output_type))

    def get_exit_code(self):
        return self.int_code

    def get_stdout(self):
        return self.output

    def get_stderr(self):
        return self.error

    @contextmanager
    def JobContext(self, logger=None):
        if logger:
            handler = JobLogHandler(100, self)
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter(fmt="%(message)s"))
            logger.addHandler(handler)

        try:
            yield
        except Exception as e:
            self.write_error(str(e))
            self.write_error(traceback.format_exc())
            self.set_status(1, status_code="error")
        finally:
            if logger:
                logger.removeHandler(handler)


class JobLogHandler(logging.handlers.BufferingHandler):
    """
    A handler that buffers log messages, and writes them to Job output
    when the buffer is full.
    """

    def __init__(self, capacity, job):
        super().__init__(capacity)

        self.job = job

    def flush(self):
        for record in self.buffer:
            message = record.getMessage()
            if record.levelno >= logging.ERROR:
                self.job.write_error(message)
            else:
                self.job.write_output(message)

        # Clear the buffer via super()
        super().flush()
