# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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

import gearman
import cPickle

try:
    import django.conf.settings as settings
except ImportError:
    class Settings:
        MCP_SERVER = ('localhost', 4730)
    settings = Settings()

class MCPClient:

    def __init__(self, host=settings.MCP_SERVER[0], port=settings.MCP_SERVER[1]):
        self.server = "%s:%d" % (host, port)

    def execute(self, uuid, choice):
        gm_client = gearman.GearmanClient([self.server])
        data = {}
        data["jobUUID"] = uuid
        data["chain"] = choice
        completed_job_request = gm_client.submit_job("approveJob", cPickle.dumps(data), None)
        #self.check_request_status(completed_job_request)
        return

    def list(self):
        gm_client = gearman.GearmanClient([self.server])
        completed_job_request = gm_client.submit_job("getJobsAwaitingApproval", "", None)
        #self.check_request_status(completed_job_request)
        return cPickle.loads(completed_job_request.result)

    def notifications(self):
        gm_client = gearman.GearmanClient([self.server])
        completed_job_request = gm_client.submit_job("getNotifications", "", None)
        #self.check_request_status(completed_job_request)
        return cPickle.loads(completed_job_request.result)

    def check_request_status(self, job_request):
        if job_request.complete:
            self.results = cPickle.loads(job_request.result)
            print "Task %s finished!  Result: %s - %s" % (job_request.job.unique, job_request.state, self.results)
        elif job_request.timed_out:
            print >>sys.stderr, "Task %s timed out!" % job_request.unique
        elif job_request.state == JOB_UNKNOWN:
            print >>sys.stderr, "Task %s connection failed!" % job_request.unique
        else:
            print >>sys.stderr, "Task %s failed!" % job_request.unique

if __name__ == '__main__':
    mcpClient = MCPClient()
    print mcpClient.list()
