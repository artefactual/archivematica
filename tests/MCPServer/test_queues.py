import concurrent.futures
import queue as Queue
import threading
import uuid
from unittest import mock

import pytest
from django.utils import timezone

from archivematica.dashboard.main import models
from archivematica.MCPServer.server import metrics
from archivematica.MCPServer.server.jobs import DecisionJob
from archivematica.MCPServer.server.jobs import Job
from archivematica.MCPServer.server.packages import DIP
from archivematica.MCPServer.server.packages import SIP
from archivematica.MCPServer.server.packages import Transfer
from archivematica.MCPServer.server.queues import FAILED_PACKAGE_TERMINAL_LINK_IDS
from archivematica.MCPServer.server.queues import TASK_EXCEPTION_MESSAGE
from archivematica.MCPServer.server.queues import PackageQueue
from archivematica.MCPServer.server.workflow import TERMINAL_PACKAGE_STATUS_FAILED
from archivematica.MCPServer.server.workflow import Link


def _process_one_job(queue):
    """Block until a job and its queue callbacks are processed.

    ``Future.result()`` waits for ``Job.run()`` to finish, but PackageQueue
    updates its active/deferred queues in done callbacks. Add a final callback
    after PackageQueue's callbacks and wait for it so assertions see the queue's
    post-callback state.
    """
    callback_ran = threading.Event()
    future = queue.process_one_job(timeout=1.0)
    future.add_done_callback(lambda _: callback_ran.set())
    future.result()
    assert callback_ran.wait(1.0)


def _process_one_failed_job(queue, exception_type):
    """Block until a failed job's cleanup callback has completed."""
    cleanup_ran = threading.Event()
    handle_job_failure = queue._handle_job_failure

    def handle_job_failure_and_signal(*args):
        try:
            return handle_job_failure(*args)
        finally:
            cleanup_ran.set()

    with mock.patch.object(
        queue, "_handle_job_failure", new=handle_job_failure_and_signal
    ):
        future = queue.process_one_job(timeout=1.0)
        with pytest.raises(exception_type):
            future.result()
        assert cleanup_ran.wait(1.0)


class MockJob(Job):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.job_ran = threading.Event()

    def run(self, *args, **kwargs):
        self.job_ran.set()


class FailingJob(MockJob):
    def run(self, *args, **kwargs):
        self.job_ran.set()
        raise KeyError("unknown Gearman job handle")


class MockDecisionJob(DecisionJob):
    """Mock Job that passes our checks for DecisionJob."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.job_ran = threading.Event()
        self.decision = None

    def run(self, *args, **kwargs):
        self.job_ran.set()
        self._awaiting_decision_event.set()

        return self

    def get_choices(self):
        return {"1": "Choice 1", "2": "Choice 2"}

    def decide(self, choice):
        self.decision = choice
        self.next_job = MockJob(self.job_chain, self.link, self.package)

        return self.next_job

    def set_active_agent(self, *args, **kwargs):
        pass


@pytest.fixture(scope="module")
def simple_executor(request):
    return concurrent.futures.ThreadPoolExecutor(max_workers=1)


@pytest.fixture
def package_queue(request, simple_executor):
    return PackageQueue(
        simple_executor, max_concurrent_packages=1, max_queued_packages=1, debug=True
    )


@pytest.fixture
def package_queue_regular(request, simple_executor):
    return PackageQueue(simple_executor, max_concurrent_packages=1, debug=True)


@pytest.fixture
def workflow_link(request):
    return Link(
        uuid.uuid4(),
        {
            "config": {
                "@manager": "linkTaskManagerDirectory",
                "@model": "StandardTaskConfig",
                "arguments": '"%fileUUID%" "%relativeLocation%" "%SIPDirectory%" "%SIPUUID%" "%taskUUID%"',
                "execute": "testLink_v0",
            },
            "description": {"en": "A Test link"},
            "exit_codes": {"0": {"job_status": "Completed successfully"}},
            "fallback_job_status": "Failed",
            "group": {"en": "Testing"},
        },
        object(),
    )


@pytest.fixture
def transfer(request, tmp_path):
    return Transfer(str(tmp_path), uuid.uuid4())


@pytest.fixture
def sip(request, tmp_path):
    return SIP(str(tmp_path), uuid.uuid4())


@pytest.fixture
def dip(request, tmp_path):
    return DIP(str(tmp_path), uuid.uuid4())


dip_1 = dip
dip_2 = dip


def test_schedule_job(package_queue, transfer, workflow_link):
    test_job = MockJob(mock.Mock(), workflow_link, transfer)

    package_queue.schedule_job(test_job)

    assert package_queue.job_queue.qsize() == 1

    _process_one_job(package_queue)

    # give ourselves up to 1 sec for other threads to spin up
    test_job.job_ran.wait(1.0)

    assert test_job.job_ran.is_set()
    assert transfer.uuid in package_queue.active_packages
    assert package_queue.job_queue.qsize() == 0
    assert package_queue.sip_queue.qsize() == 0
    assert package_queue.transfer_queue.qsize() == 0
    assert package_queue.dip_queue.qsize() == 0


def test_active_transfer_limit(package_queue, transfer, sip, workflow_link):
    test_job1 = MockJob(mock.Mock(), workflow_link, transfer)
    test_job2 = MockJob(mock.Mock(), workflow_link, sip)

    package_queue.schedule_job(test_job1)

    assert package_queue.job_queue.qsize() == 1

    # Since job 2 is part of a new package, it's delayed
    package_queue.schedule_job(test_job2)

    assert package_queue.job_queue.qsize() == 1

    _process_one_job(package_queue)

    # give ourselves up to 1 sec for other threads to spin up
    test_job1.job_ran.wait(1.0)

    assert transfer.uuid in package_queue.active_packages
    assert sip.uuid not in package_queue.active_packages
    assert package_queue.job_queue.qsize() == 0
    assert package_queue.sip_queue.qsize() == 1
    assert package_queue.transfer_queue.qsize() == 0
    assert package_queue.dip_queue.qsize() == 0


def test_activate_and_deactivate_package(package_queue, transfer):
    package_queue.activate_package(transfer)

    assert transfer.uuid in package_queue.active_packages

    package_queue.deactivate_package(transfer)

    assert transfer.uuid not in package_queue.active_packages


def test_queue_next_job_raises_full(package_queue, transfer, sip, workflow_link):
    test_job1 = MockJob(mock.Mock(), workflow_link, transfer)
    test_job2 = MockJob(mock.Mock(), workflow_link, sip)

    package_queue.schedule_job(test_job1)
    package_queue.schedule_job(test_job2)

    assert package_queue.job_queue.qsize() == 1

    with pytest.raises(Queue.Full):
        package_queue.queue_next_job()


def test_await_job_decision(package_queue, transfer, workflow_link):
    test_job = MockDecisionJob(mock.Mock(), workflow_link, transfer)
    package_queue.await_decision(test_job)

    assert package_queue.job_queue.qsize() == 0

    package_queue.decide(test_job.uuid, "1")

    assert package_queue.job_queue.qsize() == 1


def test_decision_job_moved_to_awaiting_decision(
    package_queue, transfer, sip, workflow_link
):
    test_job1 = MockDecisionJob(mock.Mock(), workflow_link, transfer)
    test_job2 = MockJob(mock.Mock(), workflow_link, sip)

    package_queue.schedule_job(test_job1)

    assert package_queue.job_queue.qsize() == 1
    _process_one_job(package_queue)
    test_job1.job_ran.wait(1.0)

    assert test_job1.job_ran.is_set()
    assert str(test_job1.uuid) in package_queue.jobs_awaiting_decisions()
    assert transfer.uuid not in package_queue.active_packages
    assert package_queue.job_queue.qsize() == 0

    package_queue.schedule_job(test_job2)
    _process_one_job(package_queue)
    test_job2.job_ran.wait(1.0)

    assert test_job2.job_ran.is_set()
    assert test_job2.uuid not in package_queue.jobs_awaiting_decisions()
    assert sip.uuid in package_queue.active_packages


def test_all_scheduled_decisions_are_processed(
    package_queue_regular, dip_1, dip_2, workflow_link
):
    package_queue = package_queue_regular

    test_job1 = MockDecisionJob(mock.Mock(), workflow_link, dip_1)
    test_job2 = MockDecisionJob(mock.Mock(), workflow_link, dip_2)

    # Schedule two jobs simultaneously.
    # We want to confirm that both are eventually processed.
    package_queue.schedule_job(test_job1)
    package_queue.schedule_job(test_job2)

    # Concurrent packages is 1, one of the two jobs must be queued.
    # The other is ready to be picked up.
    assert package_queue.job_queue.qsize() == 1
    assert package_queue.dip_queue.qsize() == 1

    # Process next job.
    _process_one_job(package_queue)
    test_job1.job_ran.wait(1.0)

    # test_job1 should be done now, queues move on.
    assert test_job1.job_ran.is_set()
    assert str(test_job1.uuid) in package_queue.jobs_awaiting_decisions()
    assert dip_1.uuid not in package_queue.active_packages
    assert package_queue.job_queue.qsize() == 1
    assert package_queue.dip_queue.qsize() == 0

    # Process next job.
    _process_one_job(package_queue)
    test_job2.job_ran.wait(1.0)

    # test_job2 should be done now, queues are empty.
    assert test_job2.job_ran.is_set()
    assert str(test_job2.uuid) in package_queue.jobs_awaiting_decisions()
    assert dip_2.uuid not in package_queue.active_packages
    assert package_queue.job_queue.qsize() == 0
    assert package_queue.dip_queue.qsize() == 0


@pytest.mark.django_db(transaction=True)
def test_all_scheduled_jobs_are_processed(
    package_queue_regular, dip_1, dip_2, workflow_link
):
    package_queue = package_queue_regular

    # Mark the link as terminal to ensure that new jobs are enqueued.
    # It causes the queue manager to hit the database.
    workflow_link._src["end"] = True

    test_job1 = MockJob(mock.Mock(), workflow_link, dip_1)
    test_job2 = MockJob(mock.Mock(), workflow_link, dip_2)

    # Schedule two jobs simultaneously.
    # We want to confirm that both are eventually processed.
    package_queue.schedule_job(test_job1)
    package_queue.schedule_job(test_job2)

    assert package_queue.job_queue.qsize() == 1
    assert package_queue.dip_queue.qsize() == 1

    _process_one_job(package_queue)

    test_job1.job_ran.wait(1.0)

    assert test_job1.job_ran.is_set()
    assert package_queue.job_queue.qsize() == 1
    assert package_queue.dip_queue.qsize() == 0

    _process_one_job(package_queue)

    test_job2.job_ran.wait(1.0)

    assert test_job2.job_ran.is_set()
    assert package_queue.job_queue.qsize() == 0
    assert package_queue.dip_queue.qsize() == 0


@pytest.mark.django_db(transaction=True)
def test_failed_terminal_link_marks_package_failed(
    package_queue, tmp_path, workflow_link
):
    package_id = uuid.uuid4()
    models.Transfer.objects.create(
        uuid=package_id,
        status=models.PACKAGE_STATUS_PROCESSING,
    )
    workflow_link._src["end"] = True
    workflow_link._src["package_status"] = TERMINAL_PACKAGE_STATUS_FAILED
    transfer = Transfer(str(tmp_path), package_id)
    test_job = MockJob(mock.Mock(), workflow_link, transfer)

    package_queue.schedule_job(test_job)
    _process_one_job(package_queue)
    test_job.job_ran.wait(1.0)

    transfer_model = models.Transfer.objects.get(pk=package_id)
    assert transfer_model.status == models.PACKAGE_STATUS_FAILED
    assert transfer_model.completed_at is not None
    assert transfer.uuid not in package_queue.active_packages


@pytest.mark.django_db(transaction=True)
def test_legacy_failed_terminal_link_marks_package_failed(
    package_queue, tmp_path, workflow_link
):
    package_id = uuid.uuid4()
    models.Transfer.objects.create(
        uuid=package_id,
        status=models.PACKAGE_STATUS_PROCESSING,
    )
    workflow_link.id = next(iter(FAILED_PACKAGE_TERMINAL_LINK_IDS))
    workflow_link._src["end"] = True
    workflow_link._src.pop("package_status", None)
    transfer = Transfer(str(tmp_path), package_id)
    test_job = MockJob(mock.Mock(), workflow_link, transfer)

    package_queue.schedule_job(test_job)
    _process_one_job(package_queue)
    test_job.job_ran.wait(1.0)

    transfer_model = models.Transfer.objects.get(pk=package_id)
    assert transfer_model.status == models.PACKAGE_STATUS_FAILED
    assert transfer_model.completed_at is not None
    assert transfer.uuid not in package_queue.active_packages


@pytest.mark.django_db(transaction=True)
def test_job_exception_fails_records_and_releases_next_package(
    package_queue, tmp_path, workflow_link, sip, caplog
):
    package_id = uuid.uuid4()
    models.Transfer.objects.create(
        uuid=package_id,
        status=models.PACKAGE_STATUS_PROCESSING,
    )
    transfer = Transfer(str(tmp_path), package_id)
    failed_job = FailingJob(mock.Mock(), workflow_link, transfer)
    queued_job = MockJob(mock.Mock(), workflow_link, sip)
    job_model = models.Job.objects.create(
        jobuuid=failed_job.uuid,
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_EXECUTING_COMMANDS,
    )
    unfinished_task = models.Task.objects.create(
        taskuuid=uuid.uuid4(),
        job=job_model,
        createdtime=timezone.now(),
    )
    completed_at = timezone.now()
    completed_task = models.Task.objects.create(
        taskuuid=uuid.uuid4(),
        job=job_model,
        createdtime=timezone.now(),
        endtime=completed_at,
        exitcode=0,
        stderror="completed",
    )

    package_queue.schedule_job(failed_job)
    package_queue.schedule_job(queued_job)

    with mock.patch.object(metrics.job_exception_counter, "inc") as counter_inc:
        _process_one_failed_job(package_queue, KeyError)

    transfer_model = models.Transfer.objects.get(pk=package_id)
    job_model.refresh_from_db()
    unfinished_task.refresh_from_db()
    completed_task.refresh_from_db()

    assert transfer_model.status == models.PACKAGE_STATUS_FAILED
    assert transfer_model.completed_at is not None
    assert job_model.currentstep == models.Job.STATUS_FAILED
    assert unfinished_task.exitcode == 1
    assert unfinished_task.endtime is not None
    assert unfinished_task.stderror == TASK_EXCEPTION_MESSAGE.format(
        job_uuid=failed_job.uuid
    )
    assert completed_task.exitcode == 0
    assert completed_task.endtime == completed_at
    assert completed_task.stderror == "completed"
    assert transfer.uuid not in package_queue.active_packages
    assert sip.uuid in package_queue.active_packages
    assert package_queue.job_queue.qsize() == 1
    assert package_queue.sip_queue.qsize() == 0
    counter_inc.assert_called_once_with()

    exception_record = next(
        record
        for record in caplog.records
        if record.message.startswith("Unexpected error processing job")
    )
    assert str(failed_job.uuid) in exception_record.message
    assert str(workflow_link.id) in exception_record.message
    assert str(transfer.uuid) in exception_record.message
    assert exception_record.exc_info[0] is KeyError


def test_terminal_job_exception_is_not_marked_done(
    package_queue, transfer, workflow_link
):
    workflow_link._src["end"] = True
    failed_job = FailingJob(mock.Mock(), workflow_link, transfer)

    with (
        mock.patch.object(failed_job, "mark_failed"),
        mock.patch(
            "archivematica.MCPServer.server.queues.Task.mark_unfinished_for_job_failed"
        ),
        mock.patch.object(transfer, "mark_as_failed") as mark_as_failed,
        mock.patch.object(transfer, "mark_as_done") as mark_as_done,
    ):
        package_queue.schedule_job(failed_job)
        _process_one_failed_job(package_queue, KeyError)

    mark_as_failed.assert_called_once_with()
    mark_as_done.assert_not_called()
    assert transfer.uuid not in package_queue.active_packages


def test_failure_cleanup_errors_do_not_block_the_next_package(
    package_queue, transfer, sip, workflow_link, caplog
):
    failed_job = FailingJob(mock.Mock(), workflow_link, transfer)
    queued_job = MockJob(mock.Mock(), workflow_link, sip)
    cleanup_error = RuntimeError("cleanup failed")

    package_queue.schedule_job(failed_job)
    package_queue.schedule_job(queued_job)

    with (
        mock.patch.object(
            metrics.job_exception_counter, "inc", side_effect=cleanup_error
        ),
        mock.patch.object(failed_job, "mark_failed", side_effect=cleanup_error),
        mock.patch(
            "archivematica.MCPServer.server.queues.Task.mark_unfinished_for_job_failed",
            side_effect=cleanup_error,
        ),
        mock.patch.object(transfer, "mark_as_failed", side_effect=cleanup_error),
    ):
        _process_one_failed_job(package_queue, KeyError)

    assert transfer.uuid not in package_queue.active_packages
    assert sip.uuid in package_queue.active_packages
    assert package_queue.job_queue.qsize() == 1
    assert (
        sum(record.message.startswith("Unable to ") for record in caplog.records) == 4
    )
