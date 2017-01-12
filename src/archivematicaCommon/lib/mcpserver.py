import sys

import grpc

from protos import mcpserver_pb2


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
        self.message = 'MCPServer client error: ' + message


class ServerUnavailableError(Error):
    def __init__(self, code):
        self.code = code
        self.message = 'server unavailable (code {})'.format(self.code)


class Client(object):
    DEFAULT_ADDRESS = 'localhost:50051'

    def __init__(self, addr=None, user_id=None, user_lang=None):
        self.addr = addr if addr is not None else self.DEFAULT_ADDRESS
        self.user_id = user_id
        self.user_lang = user_lang

        self._init_metadata()

        self.channel = grpc.insecure_channel(self.addr)
        self.stub = mcpserver_pb2.MCPServerStub(self.channel)

    def _init_metadata(self):
        metadata = list()
        if self.user_id is not None:
            metadata.append((u'user_id', unicode(self.user_id)))
        if self.user_lang is not None:
            metadata.append((u'user_lang', unicode(self.user_lang)))
        self.metadata = metadata

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
    def approve_transfer(self, id_):
        resp = self._call('ApproveTransfer', mcpserver_pb2.ApproveTransferRequest(id=id_))
        return resp.approved

    @_rendezvous_exception
    def approve_job(self, job_uuid, choice_id):
        resp = self._call('ApproveJob', mcpserver_pb2.ApproveJobRequest(id=job_uuid, choiceId=choice_id))
        return resp.approved

    @_rendezvous_exception
    def list_choices(self):
        return self._call('ChoiceList', mcpserver_pb2.ChoiceListRequest())


def get_client(**kwargs):
    if hasattr(sys.modules[__name__], 'client'):
        return getattr(sys.modules[__name__], 'client')
    client = Client(**kwargs)
    sys.modules[__name__].client = client
    return client
