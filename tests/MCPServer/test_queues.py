import concurrent.futures
import queue as Queue
import threading
import time
import uuid
from unittest import mock

import pytest
from server.jobs import DecisionJob
from server.jobs import Job
from server.packages import DIP
from server.packages import SIP
from server.packages import Transfer
from server.queues import PackageQueue
from server.workflow import Link


def _process_one_job(queue):
    """Block the thread for a little while after a job is processed.

    The goal is to let ``PackageQueue`` reach the desired state before we make
    assertions. Otherwise, these tests may eventually fail although unlikely.
    A long-term solution could be to not resolve the future until all queues
    have been updated.
    """
    queue.process_one_job(timeout=1.0).result()
    time.sleep(0.05)


class MockJob(Job):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.job_ran = threading.Event()

    def run(self, *args, **kwargs):
        self.job_ran.set()


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
