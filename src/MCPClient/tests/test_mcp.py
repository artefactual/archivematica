import time

from django.utils import timezone
import pytest

from main import models

from client.gearman import MCPGearmanWorker
from client.pool import WorkerPool


@pytest.fixture()
def mcpclient_settings(tmpdir, settings):
    ini = tmpdir.join("modules.ini")
    ini.write(
        """
[supportedBatchCommands]
assignfileuuids_v0.0 = assign_file_uuids
identifyfileformat_v0.0 = identify_file_format
"""
    )
    settings.CLIENT_MODULES_FILE = str(ini)
    settings.WORKERS = 2

    return settings


@pytest.mark.parametrize(
    "workers,cpus,expected_size",
    [
        (10, 5, 5),
        (1, 3, 1),
        (1, 1, 1),
    ],
)
def test_pool_sizing(
    mocker, mcpclient_settings, settings, workers, cpus, expected_size
):
    """The size of the pool is capped by the user setting (workers), but the
    actual value can be lower if the demand of concurrent instances is lower.
    """
    settings.WORKERS = workers
    mocker.patch("multiprocessing.cpu_count", return_value=cpus)
    mocker.patch("multiprocessing.Process")

    pool = WorkerPool()

    assert pool.pool_size == expected_size


def test_worker_arguments(mcpclient_settings, capfd):
    """Test the parameters received by spawned functions."""

    def run_worker(log_queue, client_scripts, shutdown_event=None):
        """Write to stdout so capfd can capture it. Logging would help us test
        the log listener but I couldn't make it work consistently."""
        print(client_scripts)
        shutdown_event.wait()

    pool = WorkerPool()
    pool.worker_function = run_worker
    pool.start()
    pool.stop()

    out, _ = capfd.readouterr()
    assert "['assignfileuuids_v0.0', 'identifyfileformat_v0.0']" in out
    assert "['identifyfileformat_v0.0']" in out


def test_worker_retries(mcpclient_settings):
    """Confirm that the pool is repopulated automatically."""

    def run_worker(log_queue, client_scripts, shutdown_event=None):
        shutdown_event.wait(timeout=0.1)

    pool = WorkerPool()
    pool.worker_function = run_worker
    pool.start()
    pids_1 = [w.pid for w in pool.workers]
    time.sleep(pool.WORKER_RESTART_DELAY * 2)
    pids_2 = [w.pid for w in pool.workers]
    pool.stop()

    assert pids_1 != pids_2
    assert len(pids_1) == mcpclient_settings.WORKERS
    assert len(pids_2) == mcpclient_settings.WORKERS


@pytest.mark.skip(reason="pytest doesn't support rollback emulation yet")
@pytest.mark.django_db(transaction=True)
def test_gearman_worker(mcpclient_settings):
    """Test MCPGearmanWorker.

    We're skipping this test because TransactionTestCase rolls back by
    truncating all tables, losing data populated during migrations that is
    crucial for other tests.
    """
    job = models.Job.objects.create(
        jobuuid="4f194c21-02a7-4007-ac3a-bedf476fbfc7", createdtime=timezone.now()
    )
    task_1 = models.Task.objects.create(
        taskuuid="a44093f9-cd2d-4ef8-9fce-43928ba4fb3d",
        createdtime=timezone.now(),
        job=job,
    )
    task_2 = models.Task.objects.create(
        taskuuid="780eee75-5e87-4fa0-be9f-5a430230bfbd",
        createdtime=timezone.now(),
        job=job,
    )
    task_3 = models.Task.objects.create(
        taskuuid="43f33899-9013-4694-9200-5cbb421f0596",
        createdtime=timezone.now(),
        job=job,
    )

    class FakeGearmanJob:
        unique = True

        def __init__(self, data):
            self.data = data

    class FakeModule:
        def call(self, jobs):
            jobs[0].write_output("output")
            jobs[0].set_status(0)
            jobs[1].write_error("error")
            jobs[1].set_status(1)

    class FakeFailingModule:
        def call(self, jobs):
            raise NotImplementedError("Error")

    worker = MCPGearmanWorker([], [])
    worker.job_modules["assignfileuuids_v0.0"] = FakeModule()
    worker.job_modules["identifyfileformat_v0.0"] = FakeFailingModule()

    worker.handle_job(
        "assignfileuuids_v0.0",
        None,
        FakeGearmanJob(
            {
                "tasks": {
                    task_1.taskuuid: {"arguments": "", "createdDate": ""},
                    task_2.taskuuid: {"arguments": "", "createdDate": ""},
                }
            }
        ),
    )

    try:
        worker.handle_job(
            "identifyfileformat_v0.0",
            None,
            FakeGearmanJob(
                {
                    "tasks": {
                        task_3.taskuuid: {"arguments": "", "createdDate": ""},
                    }
                }
            ),
        )
    except NotImplementedError:
        pass

    models.Task.objects.get(taskuuid=task_1.pk, exitcode=0, stdout="output")
    models.Task.objects.get(taskuuid=task_2.pk, exitcode=1, stderror="error")
    models.Task.objects.get(taskuuid=task_3.pk, exitcode=1, stderror="error")
