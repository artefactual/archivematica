"""
A Job is MCP Client's representation of a unit of work to be
performed--corresponding to a Task on the MCP Server side.  Jobs are run in
batches by clientScript modules and populated with an exit code, standard out
and standard error information.
"""

import traceback
import sys
import logging

from contextlib import contextmanager
from custom_handlers import CallbackHandler

LOGGER = logging.getLogger('archivematica.mcp.client.job')


class Job():
    def __init__(self, name, uuid, args, caller_wants_output=False):
        self.name = name
        self.UUID = uuid
        self.args = [name] + args
        self.caller_wants_output = caller_wants_output
        self.int_code = 0
        self.status_code = 'success'
        self.output = ""
        self.error = ""

    def dump(self):
        return (("#<%s; exit=%d; code=%s uuid=%s\n" +
                 "=============== STDOUT ===============\n" +
                 "%s" +
                 "\n=============== END STDOUT ===============\n" +
                 "=============== STDERR ===============\n" +
                 "%s" +
                 "\n=============== END STDERR ===============\n" +
                 "\n>") % (self.name, self.int_code, self.status_code, self.UUID, self.output, self.error))

    def load_from(self, other_job):
        self.name = other_job.name
        self.UUID = other_job.UUID
        self.args = other_job.args
        self.caller_wants_output = other_job.caller_wants_output
        self.int_code = other_job.int_code
        self.status_code = other_job.status_code
        self.output = other_job.output
        self.error = other_job.error

    def set_status(self, int_code, status_code='success'):
        if int_code:
            self.int_code = int_code
        self.status_code = status_code

    def write_output(self, s):
        self.output += s

    def write_error(self, s):
        self.error += s

    def print_output(self, *args):
        self.write_output(' '.join([str(x) for x in args]) + "\n")

    def print_error(self, *args):
        self.write_error(' '.join([str(x) for x in args]) + "\n")

    def pyprint(self, *objects, **kwargs):
        file = kwargs.get('file', sys.stdout)
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', "\n")

        msg = sep.join([str(x) for x in objects]) + end

        if file == sys.stdout:
            self.write_output(msg)
        elif file == sys.stderr:
            self.write_error(msg)
        else:
            raise Exception("Unrecognised print file: " + str(file))

    def get_exit_code(self):
        return self.int_code

    def get_stdout(self):
        return self.output

    def get_stderr(self):
        return self.error

    @contextmanager
    def JobContext(self, logger=None):
        handler = CallbackHandler(self.write_error, self.name)

        if logger:
            logger.addHandler(handler)

        try:
            yield
        except Exception as e:
            self.write_error(str(e))
            self.write_error(traceback.format_exc())
            self.set_status(1)
        finally:
            if logger:
                logger.removeHandler(handler)
