# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
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

    def execute(self, uuid, choice, uid=None):
        gm_client = gearman.GearmanClient([self.server])
        data = {}
        data["jobUUID"] = uuid
        data["chain"] = choice
        if uid != None:
            data["uid"] = uid
        completed_job_request = gm_client.submit_job("approveJob", cPickle.dumps(data), None)
        gm_client.shutdown()
        return

    def list(self):
        gm_client = gearman.GearmanClient([self.server])
        completed_job_request = gm_client.submit_job("getJobsAwaitingApproval", "", None)
        return cPickle.loads(completed_job_request.result)

    def notifications(self):
        gm_client = gearman.GearmanClient([self.server])
        completed_job_request = gm_client.submit_job("getNotifications", "", None)
        gm_client.shutdown()
        return cPickle.loads(completed_job_request.result)


if __name__ == '__main__':
    mcpClient = MCPClient()
    print mcpClient.list()
