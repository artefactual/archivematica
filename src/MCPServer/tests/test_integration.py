from __future__ import absolute_import, division, print_function, unicode_literals

import concurrent.futures
import os
import threading
import uuid

import pytest
from django.utils import six, timezone
from lxml import etree

from main import models
from server.jobs import (
    DirectoryClientScriptJob,
    FilesClientScriptJob,
    GetUnitVarLinkJob,
    JobChain,
    NextChainDecisionJob,
    OutputClientScriptJob,
    OutputDecisionJob,
    SetUnitVarLinkJob,
    UpdateContextDecisionJob,
)
from server.packages import Transfer
from server.queues import PackageQueue
from server.tasks import TaskBackend
from server.workflow import load as load_workflow


FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
INTEGRATION_TEST_PATH = os.path.join(FIXTURES_DIR, "workflow-integration-test.json")
DEFAULT_STORAGE_LOCATION = "/api/v2/location/default/"
TEST_PROCESSING_CONFIG = etree.parse(
    six.moves.StringIO(
        """<processingMCP>
  <preconfiguredChoices>
    <!-- Store DIP -->
    <preconfiguredChoice>
      <appliesTo>de6eb412-0029-4dbd-9bfa-7311697d6012</appliesTo>
      <goToChain>51e395b9-1b74-419c-b013-3283b7fe39ff</goToChain>
    </preconfiguredChoice>
  </preconfiguredChoices>
</processingMCP>
"""
    )
)


class EchoBackend(TaskBackend):
    def __init__(self):
        self.tasks = {}

    def submit_task(self, job, task):
        if job.uuid not in self.tasks:
            self.tasks[job.uuid] = []
        self.tasks[job.uuid].append(task)

    def wait_for_results(self, job):
        for task in self.tasks[job.uuid]:
            task.exit_code = 0
            task.stdout = task.arguments
            task.stderr = task.arguments
            task.finished_timestamp = timezone.now()

            yield task


@pytest.fixture
def workflow(request):
    with open(INTEGRATION_TEST_PATH) as workflow_file:
        return load_workflow(workflow_file)


@pytest.fixture
def package_queue(request):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    return PackageQueue(executor, threading.Event(), debug=True)


@pytest.fixture
def transfer(request, db):
    transfer_obj = models.Transfer.objects.create(uuid=uuid.uuid4())
    return Transfer("transfer_path", transfer_obj.uuid)


@pytest.fixture
def dummy_file_replacements(request):
    files = []
    for x in range(3):
        files.append(
            {
                r"%relativeLocation%": "transfer_path/file{}".format(x),
                r"%fileUUID%": str(uuid.uuid4()),
            }
        )

    return files


@pytest.mark.django_db(transaction=True)
def test_workflow_integration(
    mocker,
    settings,
    tmp_path,
    workflow,
    package_queue,
    transfer,
    dummy_file_replacements,
):
    # Setup our many mocks
    echo_backend = EchoBackend()
    settings.SHARED_DIRECTORY = str(tmp_path)
    settings.PROCESSING_DIRECTORY = str(tmp_path / "processing")
    mocker.patch.dict(
        "server.packages.BASE_REPLACEMENTS",
        {r"%processingDirectory%": settings.PROCESSING_DIRECTORY},
    )

    mock_get_task_backend = mocker.patch(
        "server.jobs.client.get_task_backend", return_value=echo_backend
    )
    mock_load_preconfigured_choice = mocker.patch(
        "server.jobs.decisions.load_preconfigured_choice"
    )
    mock_load_processing_xml = mocker.patch("server.jobs.decisions.load_processing_xml")
    mocker.patch.object(transfer, "files", return_value=dummy_file_replacements)

    # Schedule the first job
    first_workflow_chain = workflow.get_chains()["3816f689-65a8-4ad0-ac27-74292a70b093"]
    first_job_chain = JobChain(transfer, first_workflow_chain, workflow)
    job = next(first_job_chain)
    package_queue.schedule_job(job)

    assert package_queue.job_queue.qsize() == 1
    assert len(package_queue.active_packages) == 1
    assert transfer.uuid in package_queue.active_packages

    # Process the first job (DirectoryClientScriptJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    mock_get_task_backend.assert_called_once()
    task = echo_backend.tasks[job.uuid][0]

    assert isinstance(job, DirectoryClientScriptJob)
    assert job.exit_code == 0
    assert task.arguments == '"{}" "{}"'.format(
        settings.PROCESSING_DIRECTORY, transfer.uuid
    )

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the second job (FilesClientScriptJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    tasks = echo_backend.tasks[job.uuid]

    assert isinstance(job, FilesClientScriptJob)
    assert job.exit_code == 0
    assert len(tasks) == len(dummy_file_replacements)
    for task, replacement in zip(tasks, dummy_file_replacements):
        assert task.arguments == '"{}"'.format(replacement[r"%fileUUID%"])

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the third job (OutputClientScriptJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert isinstance(job, OutputClientScriptJob)
    assert job.exit_code == 0
    assert job.job_chain.generated_choices == {
        "default": {"description": "Default Location", "uri": DEFAULT_STORAGE_LOCATION}
    }

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Setup preconfigured choice for next job
    mock_load_preconfigured_choice.return_value = DEFAULT_STORAGE_LOCATION

    # Process the fourth job (OutputDecisionJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert isinstance(job, OutputDecisionJob)
    assert job.exit_code == 0
    assert job.job_chain.context[r"%AIPsStore%"] == DEFAULT_STORAGE_LOCATION

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Setup preconfigured choice for next job
    mock_load_preconfigured_choice.return_value = "7b814362-c679-43c4-a2e2-1ba59957cd18"

    # Process the fifth job (NextChainDecisionJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert isinstance(job, NextChainDecisionJob)
    assert job.exit_code == 0

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # We should be on chain 2 now
    assert job.job_chain is not first_job_chain
    assert job.job_chain.chain.id == "7b814362-c679-43c4-a2e2-1ba59957cd18"

    # Setup preconfigured choice for next job
    mock_load_processing_xml.return_value = TEST_PROCESSING_CONFIG

    # Process the sixth job (UpdateContextDecisionJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert isinstance(job, UpdateContextDecisionJob)
    assert job.exit_code == 0
    assert job.job_chain.context[r"%TestValue%"] == "7"

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the seventh job (SetUnitVarLinkJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert isinstance(job, SetUnitVarLinkJob)
    assert job.exit_code == 0

    unit_var = models.UnitVariable.objects.get(
        unittype=transfer.UNIT_VARIABLE_TYPE,
        unituuid=transfer.uuid,
        variable="test_unit_variable",
        variablevalue="",
        microservicechainlink="f8e4c1ee-3e43-4caa-a664-f6b6bd8f156e",
    )
    assert unit_var is not None

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the eighth job (GetUnitVarLinkJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert isinstance(job, GetUnitVarLinkJob)
    assert job.exit_code == 0

    # Out job chain should have been redirected to the final link
    assert job.job_chain.current_link.id == "f8e4c1ee-3e43-4caa-a664-f6b6bd8f156e"

    # Next job in chain should be queued
    assert package_queue.job_queue.qsize() == 1
    job = future.result()

    # Process the last job (DirectoryClientScriptJob)
    future = package_queue.process_one_job(timeout=1.0)
    concurrent.futures.wait([future], timeout=1.0)

    assert job.exit_code == 0

    # Workflow is over; we're done
    assert package_queue.job_queue.qsize() == 0
