import concurrent.futures
import os
import threading
import uuid
from io import StringIO
from unittest import mock

import pytest
from django.utils import timezone
from lxml import etree

from archivematica.dashboard.main import models
from archivematica.MCPServer.server import rpc_server
from archivematica.MCPServer.server.jobs import DirectoryClientScriptJob
from archivematica.MCPServer.server.jobs import FilesClientScriptJob
from archivematica.MCPServer.server.jobs import GetUnitVarLinkJob
from archivematica.MCPServer.server.jobs import JobChain
from archivematica.MCPServer.server.jobs import NextChainDecisionJob
from archivematica.MCPServer.server.jobs import OutputClientScriptJob
from archivematica.MCPServer.server.jobs import OutputDecisionJob
from archivematica.MCPServer.server.jobs import SetUnitVarLinkJob
from archivematica.MCPServer.server.jobs import UpdateContextDecisionJob
from archivematica.MCPServer.server.packages import PACKAGE_TYPE_STARTING_POINTS
from archivematica.MCPServer.server.packages import Transfer
from archivematica.MCPServer.server.packages import create_package
from archivematica.MCPServer.server.queues import PackageQueue
from archivematica.MCPServer.server.tasks import Task
from archivematica.MCPServer.server.tasks import TaskBackend
from archivematica.MCPServer.server.workflow import load as load_workflow

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
INTEGRATION_TEST_PATH = os.path.join(FIXTURES_DIR, "workflow-integration-test.json")
DEFAULT_STORAGE_LOCATION = "/api/v2/location/default/"
RETRIEVAL_LINK_ID = "b3843201-3c52-4124-a7ee-16faaccf24b9"
# A minimal processing configuration used by the pre-existing workflow exercise.
TEST_PROCESSING_CONFIG = etree.parse(
    StringIO(
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
    """Return task arguments as successful output for workflow traversal tests."""

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


class ControlledBackend(TaskBackend):
    """Persist tasks and return deterministic results after an optional pause."""

    def __init__(self, results=None, on_success=None):
        self.results = results or {}
        self.on_success = on_success
        self.tasks = {}
        self.started = threading.Event()
        self.release = threading.Event()

    def submit_task(self, job, task):
        self.tasks.setdefault(job.uuid, []).append(task)
        Task.bulk_log([task], job)
        models.Task.objects.filter(taskuuid=task.uuid).update(
            starttime=task.start_timestamp
        )

    def wait_for_results(self, job):
        if job.name == "retrievetransfersource_v0.0":
            self.started.set()
            if not self.release.wait(timeout=5):
                raise TimeoutError("Timed out waiting to release retrieval task")

        exit_code, stderr = self.results.get(job.name, (0, ""))
        for task in self.tasks[job.uuid]:
            task.exit_code = exit_code
            task.stderr = stderr
            task.finished_timestamp = timezone.now()
            models.Task.objects.filter(taskuuid=task.uuid).update(
                exitcode=exit_code,
                stderror=stderr,
                endtime=task.finished_timestamp,
            )
            if exit_code == 0 and self.on_success is not None:
                self.on_success(job)
            yield task


def _submit_synchronously(fn, *args, **kwargs):
    """Emulate Executor.submit while running bootstrap work deterministically."""
    future = concurrent.futures.Future()
    try:
        future.set_result(fn(*args, **kwargs))
    except BaseException as err:
        future.set_exception(err)
    return future


def _future_result(future):
    """Resolve workflow work with a bounded wait so failures cannot hang tests."""
    return future.result(timeout=5)


@pytest.fixture
def workflow():
    with open(INTEGRATION_TEST_PATH) as workflow_file:
        return load_workflow(workflow_file)


@pytest.fixture
def package_queue():
    """Own a one-worker PackageQueue and always release its executor."""
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        yield PackageQueue(executor, threading.Event(), debug=True)
    finally:
        executor.shutdown(wait=True)


@pytest.fixture
def transfer(db):
    transfer_obj = models.Transfer.objects.create(uuid=uuid.uuid4())
    return Transfer("transfer_path", transfer_obj.uuid)


@pytest.fixture
def dummy_file_replacements():
    files = []
    for x in range(3):
        files.append(
            {
                r"%relativeLocation%": f"transfer_path/file{x}",
                r"%fileUUID%": str(uuid.uuid4()),
            }
        )

    return files


@pytest.fixture
def controlled_backend_factory(package_queue):
    """Build controllable backends and release them before executor teardown."""
    backends = []

    def make(*args, **kwargs):
        backend = ControlledBackend(*args, **kwargs)
        backends.append(backend)
        return backend

    yield make

    # Release blocked retrievals before the package queue shuts its executor down.
    for backend in backends:
        backend.release.set()


@pytest.mark.django_db(transaction=True)
@mock.patch("archivematica.MCPServer.server.jobs.decisions.load_processing_xml")
@mock.patch("archivematica.MCPServer.server.jobs.decisions.load_preconfigured_choice")
@mock.patch("archivematica.MCPServer.server.jobs.client.get_task_backend")
def test_workflow_integration(
    mock_get_task_backend,
    mock_load_preconfigured_choice,
    mock_load_processing_xml,
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
    mock_get_task_backend.return_value = echo_backend

    with (
        mock.patch.dict(
            "archivematica.MCPServer.server.packages.BASE_REPLACEMENTS",
            {r"%processingDirectory%": settings.PROCESSING_DIRECTORY},
        ),
        mock.patch.object(transfer, "files", return_value=dummy_file_replacements),
    ):
        # Schedule the first job
        first_workflow_chain = workflow.get_chains()[
            "3816f689-65a8-4ad0-ac27-74292a70b093"
        ]
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
        assert task.arguments == f'"{settings.PROCESSING_DIRECTORY}" "{transfer.uuid}"'

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
            "default": {
                "description": "Default Location",
                "uri": DEFAULT_STORAGE_LOCATION,
            }
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
        mock_load_preconfigured_choice.return_value = (
            "7b814362-c679-43c4-a2e2-1ba59957cd18"
        )

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


@pytest.mark.django_db(transaction=True)
@mock.patch("archivematica.MCPServer.server.jobs.client.get_task_backend")
def test_transfer_source_retrieval_is_visible_and_continues_workflow(
    get_task_backend,
    admin_user,
    wf,
    retrieval_directories,
    package_queue,
    controlled_backend_factory,
):
    """A running retrieval is observable and resumes the type-specific chain."""
    final_path = retrieval_directories.processing / "TransferName"

    def complete_retrieval(job):
        final_path.mkdir(exist_ok=True)
        models.Transfer.objects.filter(uuid=job.package.uuid).update(
            currentlocation="%sharedPath%currentlyProcessing/TransferName"
        )

    backend = controlled_backend_factory(on_success=complete_retrieval)
    get_task_backend.return_value = backend
    bootstrap_executor = mock.Mock()
    bootstrap_executor.submit.side_effect = _submit_synchronously

    transfer = create_package(
        package_queue,
        bootstrap_executor,
        "TransferName",
        "standard",
        "",
        "",
        "source-location:/transfer/source/path",
        "",
        admin_user.pk,
        wf,
        auto_approve=True,
    )

    retrieval_future = package_queue.process_one_job(timeout=1)
    assert backend.started.wait(timeout=1)

    retrieval_job = models.Job.objects.get(sipuuid=transfer.uuid)
    retrieval_task = models.Task.objects.get(job=retrieval_job)
    assert str(retrieval_job.microservicechainlink) == RETRIEVAL_LINK_ID
    assert retrieval_job.currentstep == models.Job.STATUS_EXECUTING_COMMANDS
    assert retrieval_task.exitcode is None

    shutdown_event = threading.Event()
    shutdown_event.set()
    server = rpc_server.RPCServer(
        wf,
        shutdown_event,
        package_queue,
        package_queue.executor,
    )
    units = server._units_statuses_handler(
        None,
        None,
        {"type": "Transfer", "lang": "en"},
    )
    unit = next(item for item in units if item["uuid"] == transfer.uuid)
    assert unit["active"] is True
    assert unit["jobs"][0]["link_id"] == RETRIEVAL_LINK_ID
    assert unit["jobs"][0]["currentstep"] == models.Job.STATUS_EXECUTING_COMMANDS
    assert (
        server._unit_status_handler(
            None,
            None,
            {"id": str(transfer.uuid), "lang": "en"},
        )["jobs"][0]["description"]
        == "Retrieve transfer source"
    )

    backend.release.set()
    continuation_job = _future_result(retrieval_future)
    retrieval_job.refresh_from_db()
    retrieval_task.refresh_from_db()
    transfer.refresh_from_db()
    assert retrieval_job.currentstep == models.Job.STATUS_COMPLETED_SUCCESSFULLY
    assert retrieval_task.exitcode == 0
    assert transfer.currentlocation == "%sharedPath%currentlyProcessing/TransferName"

    continuation_future = package_queue.process_one_job(timeout=1)
    next_job = _future_result(continuation_future)
    assert isinstance(continuation_job, GetUnitVarLinkJob)
    assert next_job.link.id == PACKAGE_TYPE_STARTING_POINTS["standard"].link
    assert package_queue.job_queue.qsize() == 1


@pytest.mark.django_db(transaction=True)
@mock.patch("archivematica.MCPServer.server.jobs.client.get_task_backend")
def test_transfer_source_retrieval_failure_routes_to_failed_transfer(
    get_task_backend,
    admin_user,
    wf,
    retrieval_directories,
    package_queue,
    controlled_backend_factory,
):
    """A failed retrieval follows cleanup and never enters normal processing."""
    backend = controlled_backend_factory(
        results={
            "retrievetransfersource_v0.0": (
                1,
                "Storage Service copy timed out",
            )
        }
    )
    backend.release.set()
    get_task_backend.return_value = backend
    bootstrap_executor = mock.Mock()
    bootstrap_executor.submit.side_effect = _submit_synchronously

    transfer = create_package(
        package_queue,
        bootstrap_executor,
        "TransferName",
        "standard",
        "",
        "",
        "source-location:/transfer/source/path",
        "",
        admin_user.pk,
        wf,
        auto_approve=True,
    )

    retrieval_future = package_queue.process_one_job(timeout=1)
    _future_result(retrieval_future)
    retrieval_job = models.Job.objects.get(
        sipuuid=transfer.uuid,
        microservicechainlink=RETRIEVAL_LINK_ID,
    )
    retrieval_task = models.Task.objects.get(job=retrieval_job)
    assert retrieval_job.currentstep == models.Job.STATUS_FAILED
    assert retrieval_task.exitcode == 1
    assert retrieval_task.stderror == "Storage Service copy timed out"

    failed_cleanup_future = package_queue.process_one_job(timeout=1)
    _future_result(failed_cleanup_future)
    move_failed_future = package_queue.process_one_job(timeout=1)
    _future_result(move_failed_future)

    jobs = models.Job.objects.filter(sipuuid=transfer.uuid)
    assert jobs.filter(microservicegroup="Failed transfer").exists()
    assert not jobs.filter(
        microservicechainlink=PACKAGE_TYPE_STARTING_POINTS["standard"].link
    ).exists()
