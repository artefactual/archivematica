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
