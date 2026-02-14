import threading
import uuid
from unittest import mock

import pytest
from django.utils import timezone

from archivematica.dashboard.main import models
from archivematica.MCPServer.server import rpc_server
from archivematica.MCPServer.server.jobs.chain import get_job_class_for_link

TASK_PRODUCING_LINK_ID = "002716a1-ae29-4f36-98ab-0d97192669c4"


@pytest.mark.django_db
def test_approve_partial_reingest_handler(wf):
    sip = models.SIP.objects.create(uuid=str(uuid.uuid4()))
    models.Job.objects.create(
        sipuuid=sip.pk,
        microservicegroup="Reingest AIP",
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_AWAITING_DECISION,
    )
    package_queue = mock.MagicMock()
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    server._approve_partial_reingest_handler(None, wf, {"sip_uuid": sip.pk})

    package_queue.decide.assert_called_once()


@pytest.mark.django_db
def test_units_statuses_handler_sets_produces_tasks_from_job_class(wf):
    task_producing_link = wf.get_link(TASK_PRODUCING_LINK_ID)
    assert get_job_class_for_link(task_producing_link).produces_tasks is True

    sip = models.SIP.objects.create(uuid=str(uuid.uuid4()))
    models.Job.objects.create(
        sipuuid=sip.pk,
        unittype="unitSIP",
        microservicegroup="Test group",
        microservicechainlink=task_producing_link.id,
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_EXECUTING_COMMANDS,
    )

    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._units_statuses_handler(None, None, {"type": "SIP", "lang": "en"})

    assert len(response) == 1
    assert len(response[0]["jobs"]) == 1
    assert response[0]["jobs"][0]["produces_tasks"] is True
