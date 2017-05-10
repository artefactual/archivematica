from concurrent import futures
import logging
import time
import timeit

import grpc
import six

from django.core.exceptions import ObjectDoesNotExist

# This import is important! It's here so jobChain is imported before
# linkTaskManagerChoice is imported. The old RPCServer module was doing the
# same but it was not documented. This is easy to fix but it requires some
# refactoring - assure that archivematicaMCP is not imported by other modules,
# which is possible if we move config globals to its own module.
import archivematicaMCP

from main.models import Job, SIP, Transfer
from protos import mcpserver_pb2


logger = logging.getLogger('archivematica.mcp.server.grpc')

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def _log_rpc(func):
    def _decorated(*args, **kwargs):
        logger.debug("rpc %s | Request received", func.func_name)
        start_time = timeit.default_timer()
        request = args[1]
        for name, _ in six.iteritems(request.DESCRIPTOR.fields_by_camelcase_name):
            # Unpacked, but I don't need the `google.protobuf.descriptor.FieldDescriptor` for now
            try:
                value = getattr(request, name)
            except AttributeError:
                logger.debug("rpc %s | Parameter %s received but it is unknown? (type %s)", func.func_name, name, type(value).__name__)
            else:
                logger.debug("rpc %s | Parameter %s received (type %s)", func.func_name, name, type(value).__name__)
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = 1000 * (timeit.default_timer() - start_time)
            logger.debug("rpc %s | Response sent (processing time: %.2fms)", func.func_name, elapsed)
    return _decorated


# Map the internal linkTaskManager unitType attribute to our proto values
_UNIT_TYPES = {
    'SIP': mcpserver_pb2.ChoiceListResponse.Job.UnitType.Value('INGEST'),
    'Transfer': mcpserver_pb2.ChoiceListResponse.Job.UnitType.Value('TRANSFER'),
    'DIP': mcpserver_pb2.ChoiceListResponse.Job.UnitType.Value('DIP'),
}


class gRPCServer(object):
    def __init__(self, workflow, unit_choices):
        self.workflow = workflow
        self.unit_choices = unit_choices

    @_log_rpc
    def ApproveJob(self, request, context):
        """
        Approve the job requested only if avaiable.
        """
        metadata = dict(context.invocation_metadata())
        resp = mcpserver_pb2.ApproveJobResponse()
        with self.unit_choices:
            try:
                self.unit_choices[request.id].proceed_with_choice(request.choiceId, user_id=metadata['user_id'])
            except KeyError:
                logger.error('The job could not be approved (choice=%s)', request.choiceId, exc_info=True)
                return resp
        resp.approved = True
        return resp

    @_log_rpc
    def ApproveTransfer(self, request, context):
        """
        Look up the transfer given its UUID. Proceed only if the choice is a
        'Approve transfer'.
        """
        metadata = dict(context.invocation_metadata())
        resp = mcpserver_pb2.ApproveTransferResponse()
        match = None
        with self.unit_choices:
            for job_uuid, task_manager in self.unit_choices.items():
                unit_uuid = task_manager.unit.UUID
                if request.id != unit_uuid:
                    continue
                for item in task_manager.choices:
                    value = item[0]
                    try:
                        description = item[1]['en']
                    except KeyError:
                        continue
                    if description != 'Approve transfer':
                        continue
                    match = task_manager
                    break
            if match is None:
                return resp
            match.proceed_with_choice(value, user_id=metadata['user_id'])
            resp.approved = True
        return resp

    @_log_rpc
    def ChoiceList(self, request, context):
        metadata = dict(context.invocation_metadata())
        resp = mcpserver_pb2.ChoiceListResponse()

        units_visited = {'Transfer': [], 'SIP': [], 'DIP': []}
        with self.unit_choices:
            for job_uuid, task_manager in self.unit_choices.items():
                if task_manager.unit.unitType not in ('Transfer', 'SIP', 'DIP'):
                    continue

                # Look up the database to see if the unit is hidden
                try:
                    if task_manager.unit.unitType in ('DIP', 'SIP'):
                        unit = SIP.objects.get(pk=task_manager.unit.UUID)
                    else:
                        unit = Transfer.objects.get(pk=task_manager.unit.UUID)
                except ObjectDoesNotExist:
                    # Omit if it's not in the database
                    continue
                else:
                    if unit.hidden:
                        continue

                units_visited[task_manager.unit.unitType].append(job_uuid if task_manager.unit.unitType == 'DIP' else task_manager.unit.UUID)

                # Populate choices
                job = resp.jobs.add()
                job.id = job_uuid
                job.unitType = _UNIT_TYPES.get(task_manager.unit.unitType)
                for item in task_manager.choices:
                    choice = job.choices.add()
                    choice.value = str(item[0])
                    choice.description = get_translation(item[1], metadata['user_lang'])

        resp.transferCount = len(units_visited['Transfer'])
        resp.ingestCount = len(units_visited['SIP'])

        # Only count a DIP if its respective SIP has not be already included.
        # The reason we are doing this is that DIPs are also considered SIPs
        # in the Archivematica data model.
        for job in Job.objects.filter(jobuuid__in=units_visited['DIP']):
            if job.jobuuid not in units_visited['SIP']:
                resp.ingestCount = resp.ingestCount + 1

        return resp


def get_translation(field, lang, default='en'):
    return field.get(lang, default)


def start(workflow, unit_choices):
    """
    Start our gRPC server with which our RPCs can be serviced. We pass our own
    pool of threads (futures.ThreadPoolExecutor) that we want the server to use
    to service the RPCs.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    mcpserver_pb2.add_MCPServerServicer_to_server(gRPCServer(workflow, unit_choices), server)

    # We can afford to do this as long as Archivematica runs in a box.
    # Hoping not to do that for much longer though.
    addr = '[::]:50051'
    server.add_insecure_port(addr)
    logger.info('gRPC server listening on %s', addr)

    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
