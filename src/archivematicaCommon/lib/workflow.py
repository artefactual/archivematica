import sys

import grpc

from protos import workflow_pb2


DEFAULT_ADDRESS = 'localhost:50050'


def _rendezvous_exception(func):
    def _decorated(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except grpc._channel._Rendezvous, e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ClientUnavailableError(e.code())
    return _decorated


class ClientError(Exception):
    pass


class ClientUnavailableError(ClientError):
    def __init__(self, code):
        self.code = code


class Client(object):
    def __init__(self, addr=None):
        addr = addr if addr is not None else DEFAULT_ADDRESS
        self.channel = grpc.insecure_channel(addr)
        self.stub = workflow_pb2.WorkflowStub(self.channel)

    @_rendezvous_exception
    def get_workflow(self, id_):
        resp = self.stub.WorkflowGet(workflow_pb2.WorkflowGetRequest(id=id_))
        if resp.error != '':
            raise ClientError(resp.error)
        return resp.workflow


def get_client(address=None):
    if hasattr(sys.modules[__name__], 'client'):
        return getattr(sys.modules[__name__], 'client')
    client = Client(address)
    sys.modules[__name__].client = client
    return client
