import sys

import grpc

from protos import mcpserver_pb2


DEFAULT_ADDRESS = 'localhost:50051'


class ClientError(Exception):
    pass


class Client(object):
    def __init__(self, addr=None):
        addr = addr if addr is not None else DEFAULT_ADDRESS
        self.channel = grpc.insecure_channel(addr)
        self.stub = mcpserver_pb2.MCPServerStub(self.channel)

    def approve_transfer(self, id_):
        resp = self.stub.ApproveTransfer(mcpserver_pb2.ApproveTransferRequest(id=id_))
        return resp.approved

    def approve_job(self, job_uuid, choice_id):
        resp = self.stub.ApproveJob(mcpserver_pb2.ApproveJobRequest(id=job_uuid, choiceId=choice_id))
        return resp.approved

    def list_choices(self):
        return self.stub.ChoiceList(mcpserver_pb2.ChoiceListRequest())


def get_client(address=None):
    if hasattr(sys.modules[__name__], 'client'):
        return getattr(sys.modules[__name__], 'client')
    client = Client(address)
    sys.modules[__name__].client = client
    return client
