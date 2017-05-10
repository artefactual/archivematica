import sys

import grpc

from protos import workflow_pb2


def _rendezvous_exception(func):
    def _decorated(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except grpc._channel._Rendezvous as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ServerUnavailableError(e.code())
    return _decorated


class Error(Exception):
    def __init__(self, message):
        self.message = 'Workflow client error: ' + message


class ServerUnavailableError(Error):
    def __init__(self, code):
        self.code = code
        self.message = 'server unavailable, code ' + self.code


class Client(object):
    DEFAULT_ADDRESS = 'localhost:50050'

    def __init__(self, addr=None):
        self.addr = addr if addr is not None else self.DEFAULT_ADDRESS

        self._init_metadata()

        self.channel = grpc.insecure_channel(self.addr)
        self.stub = workflow_pb2.WorkflowStub(self.channel)

    def _init_metadata(self):
        self.metadata = list()

    def _call(self, method, request, metadata=None):
        """
        Shortcut caller of stub methods passing client metadata. Extra metadata
        can be passed at call time.
        """
        mdata = self.metadata
        if isinstance(metadata, list):
            mdata += metadata
        return getattr(self.stub, method)(request, metadata=mdata)

    @_rendezvous_exception
    def get_workflow(self, id_):
        resp = self._call('WorkflowGet', workflow_pb2.WorkflowGetRequest(id=id_))
        if resp.error != '':
            raise Error(resp.error)
        return resp.workflow


def get_client(addr=None):
    if hasattr(sys.modules[__name__], 'client'):
        return getattr(sys.modules[__name__], 'client')
    client = Client(addr)
    sys.modules[__name__].client = client
    return client
