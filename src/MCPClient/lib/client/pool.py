"""Worker pool.

WorkerPool is the core of MCPClient, a pool of system processes that are
independent Gearman workers. Only one process in the pool will handle tasks
unless marked as safe for concurrent instances.

The pool ensures that processes are replaced when they fail or exit. The max.
number or processes allowed in the pool can be established with the ``workers``
setting. Workers can also be programmed to perform a limited number of tasks
with ``max_tasks_per_child``, which is useful to free resources held.

Workers log events into a shared queue while the pool runs a background thread
(log listener) that listens to the queue and writes the events safely.

The parent treats worker process liveness and Gearman readiness as separate
states. A child can be alive but unusable if it has not reached the point where
it has connected to Gearman and flushed its startup commands. The pool tracks
that readiness explicitly so failed replacements are restarted instead of
leaving a live-but-unregistered worker slot in place.
"""

import faulthandler
import logging
import logging.handlers
import multiprocessing
import os
import queue
import signal
import threading
import time
from enum import Enum
from multiprocessing.synchronize import Event
from types import ModuleType
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Protocol
from typing import Tuple
from typing import TypeVar
from typing import cast

import django

django.setup()

from django import db
from django.conf import settings

from client import loader
from client import metrics
from client.gearman import MCPGearmanWorker

T = TypeVar("T")


class QueueLike(Protocol[T]):
    def get(self, block: bool = True, timeout: Optional[float] = None) -> T: ...
    def get_nowait(self) -> T: ...
    def put_nowait(self, item: T) -> None: ...


LogQueue = QueueLike[logging.LogRecord]
WorkerReadyQueue = QueueLike["WorkerReadyMessage"]

# Use forkserver so workers are not forked directly from the long-lived parent.
# The parent has threads for logging, metrics, and pool maintenance; forking a
# process with active threads and inherited locks is fragile. Forkserver still
# gives us process isolation while starting children from a simpler process.
MP_CONTEXT = multiprocessing.get_context("forkserver")

# This is how the return value of the `_get_worker_init_args` method looks
# below:
# [
#     (
#         (
#             "<multiprocessing.queues.Queue object at 0x7609ba4badf0>",
#             [
#                 "archivematicaclamscan_v0.0",
#                 "examinecontents_v0.0",
#                 "identifyfileformat_v0.0",
#                 "transcribefile_v0.0",
#                 "characterizefile_v0.0",
#             ],
#             0,
#         ),
#         {
#             "shutdown_event": "<multiprocessing.synchronize.Event object at 0x7609ba454340>"
#         },
#     ),
#     ...
# ]
WorkerInitArgs = List[
    Tuple[Tuple[LogQueue, WorkerReadyQueue, List[str], int], Dict[str, Event]]
]

logger = logging.getLogger("archivematica.mcp.client.worker")


class WorkerReadyMessage(NamedTuple):
    """Readiness notification sent by a child worker to the parent.

    This does not mean only "the process started". It means the child reached
    MCPClient's readiness boundary and should be considered available for its
    worker slot if the PID still matches the currently tracked process.
    """

    worker_index: int
    process_id: int


class WorkerState(str, Enum):
    """Parent-observed state for one worker slot."""

    STARTING = "starting"
    READY = "ready"
    EXITED = "exited"
    UNREADY_TIMEOUT = "unready_timeout"


def _register_traceback_dump_handler() -> None:
    """Let the parent request a Python stack dump from a stuck child."""
    if not hasattr(signal, "SIGUSR1"):
        logger.debug("SIGUSR1 is not available; worker traceback dumps disabled")
        return

    try:
        faulthandler.register(signal.SIGUSR1, all_threads=True, chain=False)
    except (OSError, RuntimeError, ValueError) as err:
        logger.warning("Could not register worker traceback dump handler: %s", err)


def run_gearman_worker(
    log_queue: LogQueue,
    readiness_queue: WorkerReadyQueue,
    client_scripts: List[str],
    worker_index: int,
    shutdown_event: Optional[Event] = None,
) -> None:
    """Target function executed by child processes in the pool.

    Each child configures queue-backed logging and metrics, closes inherited
    database connections, builds its own Gearman worker, and reports readiness
    only through the Gearman worker's readiness callback.
    """
    # Child processes should not inherit MCPClient parent signal handlers. Keep
    # SIGTERM terminable by Process.terminate(), and let SIGINT use Python's
    # normal KeyboardInterrupt behavior.
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.default_int_handler)
    _register_traceback_dump_handler()

    process_id = multiprocessing.current_process().pid
    if process_id is None:
        raise RuntimeError("Worker process has no PID")

    max_jobs_to_process = settings.MAX_TASKS_PER_CHILD

    # Set up logging, as we're in a new process now.
    logger = logging.getLogger("archivematica.mcp.client")
    logger.setLevel(logging.DEBUG)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(queue_handler)

    gearman_hosts = [settings.GEARMAN_SERVER]

    # Reject connections of the parent, this process will have its own.
    db.connections.close_all()

    def report_ready() -> None:
        readiness_queue.put_nowait(WorkerReadyMessage(worker_index, process_id))

    worker = MCPGearmanWorker(
        gearman_hosts,
        client_scripts,
        shutdown_event=shutdown_event,
        max_jobs_to_process=max_jobs_to_process,
        readiness_callback=report_ready,
    )
    logger.debug("Worker process %s starting", process_id)
    try:
        worker.work()
    finally:
        logger.debug("Worker process %s exiting", process_id)


class WorkerPool:
    # Delay in the maintenance loop until workers are checked and restarted.
    WORKER_RESTART_DELAY = 1.0
    # Workers normally register Gearman tasks quickly. A worker that remains
    # alive but unready after this timeout is treated as a failed replacement.
    WORKER_STARTUP_TIMEOUT = 30.0
    # Time to wait after SIGTERM before killing an unready worker.
    WORKER_TERMINATE_TIMEOUT = 5.0
    WORKER_TRACEBACK_DUMP_DELAY = 0.5

    def __init__(self) -> None:
        self.log_queue: LogQueue = MP_CONTEXT.Queue()
        self.worker_readiness_queue: WorkerReadyQueue = MP_CONTEXT.Queue()
        self.shutdown_event = MP_CONTEXT.Event()
        self.workers: List[multiprocessing.Process] = []

        # Slot state is owned by the parent. ``worker_ready`` maps slot -> PID
        # so a delayed readiness message from an already-replaced child cannot
        # mark the new process ready by accident.
        self.worker_started_at: Dict[int, float] = {}
        self.worker_ready_at: Dict[int, float] = {}
        self.worker_ready: Dict[int, int] = {}
        self.worker_state: Dict[int, WorkerState] = {}
        self.job_modules = loader.load_job_modules(settings.CLIENT_MODULES_FILE)
        self.worker_function = run_gearman_worker

        # The max. number of workers is established by the ``workers`` setting,
        # but the final number of workers may be lower (but not higher) meeting
        # the demand of client modules and ``concurrent_instances``.`
        workers_required = self._get_script_workers_required(self.job_modules)
        self.pool_size = min(settings.WORKERS, max(workers_required.values()))
        self._worker_init_args = self._get_worker_init_args(workers_required)

        self.pool_maintainance_thread: Optional[threading.Thread] = None
        self.logging_listener: Optional[logging.handlers.QueueListener] = None

    def start(self) -> None:
        self.logging_listener = logging.handlers.QueueListener(
            self.log_queue,
            *logger.handlers,
            respect_handler_level=True,
        )
        self.logging_listener.start()

        for i in range(self.pool_size - len(self.workers)):
            worker = self._start_worker(i)
            self.workers.append(worker)

        self.pool_maintainance_thread = threading.Thread(target=self._maintain_pool)
        self.pool_maintainance_thread.daemon = True
        self.pool_maintainance_thread.start()

    def stop(self) -> None:
        self.shutdown_event.set()
        if self.pool_maintainance_thread is not None:
            self.pool_maintainance_thread.join()

        for worker in self.workers:
            if worker.is_alive():
                worker.join(0.1)

        for worker in self.workers:
            if worker.is_alive():
                worker.terminate()

        for worker in self.workers:
            if not worker.is_alive():
                metrics.worker_exit(worker.pid)

        if self.logging_listener is not None:
            self.logging_listener.stop()

    def _get_script_workers_required(
        self, job_modules: Dict[str, Optional[ModuleType]]
    ) -> Dict[str, int]:
        workers_required = {}
        for client_script, module in job_modules.items():
            concurrency = loader.get_module_concurrency(module)
            workers_required[client_script] = concurrency

        return workers_required

    # Use Queue[logging.LogRecord] instead of Any
    def _get_worker_init_args(
        self, script_workers_required: Dict[str, int]
    ) -> WorkerInitArgs:
        # Don't mutate the argument
        script_workers_required = script_workers_required.copy()
        init_scripts: List[List[str]] = []

        for i in range(self.pool_size):
            init_scripts.append([])
            for script_name, workers_remaining in script_workers_required.items():
                if workers_remaining > 0:
                    init_scripts[i].append(script_name)
                    script_workers_required[script_name] -= 1

        return [
            (
                (
                    self.log_queue,
                    self.worker_readiness_queue,
                    worker_init_scripts,
                    index,
                ),
                {
                    "shutdown_event": self.shutdown_event,
                },
            )
            for index, worker_init_scripts in enumerate(init_scripts)
        ]

    def _maintain_pool(self) -> None:
        """Run the worker supervision loop in the parent process.

        The loop drains readiness messages and replaces workers that have
        exited or remained alive without reaching readiness.
        """
        while not self.shutdown_event.is_set():
            self._collect_worker_readiness()
            self._restart_exited_workers()
            self._restart_unready_workers()
            time.sleep(self.WORKER_RESTART_DELAY)

    def _restart_exited_workers(self) -> bool:
        """Restart any worker processes which have exited due to reaching
        their specified lifetime.  Returns True if any workers were restarted.
        """
        restarted = False
        for index, worker in enumerate(self.workers):
            if worker.exitcode is not None:
                self.worker_state[index] = WorkerState.EXITED
                self.worker_ready.pop(index, None)
                self.worker_ready_at.pop(index, None)
                logger.info(
                    "Worker slot %s process %s exited with code %s; restarting",
                    index,
                    worker.pid,
                    worker.exitcode,
                )
                metrics.worker_exit(worker.pid)
                worker.join()
                restarted = True
                self.workers[index] = self._start_worker(index)

        return restarted

    def _collect_worker_readiness(self) -> None:
        """Accept readiness messages from the current process in each slot.

        Replacement can race with child startup. A stale child may report ready
        after the parent has already put a new process in the same slot, so the
        PID in the message must match the currently tracked worker PID.
        """
        while True:
            try:
                message = self.worker_readiness_queue.get_nowait()
            except queue.Empty:
                return

            if message.worker_index >= len(self.workers):
                logger.debug(
                    "Ignoring readiness from unknown worker index %s (pid %s)",
                    message.worker_index,
                    message.process_id,
                )
                continue

            current_worker = self.workers[message.worker_index]
            if current_worker.pid != message.process_id:
                logger.debug(
                    "Ignoring stale readiness from worker index %s pid %s; current pid is %s",
                    message.worker_index,
                    message.process_id,
                    current_worker.pid,
                )
                continue

            now = time.monotonic()
            started_at = self.worker_started_at.get(message.worker_index)
            if started_at is not None:
                logger.info(
                    "Worker slot %s process %s reported ready after %.3f seconds",
                    message.worker_index,
                    message.process_id,
                    now - started_at,
                )
            else:
                logger.info(
                    "Worker slot %s process %s reported ready",
                    message.worker_index,
                    message.process_id,
                )
            self.worker_ready[message.worker_index] = message.process_id
            self.worker_ready_at[message.worker_index] = now
            self.worker_state[message.worker_index] = WorkerState.READY

    def _restart_unready_workers(self) -> bool:
        """Restart workers that are alive but never reached readiness.

        This handles the failure mode where process supervision alone is not
        enough: the OS process exists, but the worker did not complete Gearman
        initialization and therefore cannot take tasks.
        """
        restarted = False
        now = time.monotonic()
        for index, worker in enumerate(self.workers):
            if worker.exitcode is not None:
                continue

            if self.worker_ready.get(index) == worker.pid:
                continue

            started_at = self.worker_started_at.get(index)
            if started_at is None or now - started_at < self.WORKER_STARTUP_TIMEOUT:
                continue

            logger.warning(
                "Worker slot %s process %s did not report ready within %.1f seconds; restarting",
                index,
                worker.pid,
                self.WORKER_STARTUP_TIMEOUT,
            )
            self.worker_state[index] = WorkerState.UNREADY_TIMEOUT
            self.worker_ready.pop(index, None)
            self.worker_ready_at.pop(index, None)
            self._dump_unready_worker_traceback(index, worker)
            worker.terminate()
            worker.join(self.WORKER_TERMINATE_TIMEOUT)
            if worker.is_alive():
                logger.error(
                    "Worker slot %s process %s did not terminate; killing",
                    index,
                    worker.pid,
                )
                worker.kill()
                worker.join()

            metrics.worker_exit(worker.pid)
            self.workers[index] = self._start_worker(index)
            restarted = True

        return restarted

    def _dump_unready_worker_traceback(
        self, index: int, worker: multiprocessing.Process
    ) -> None:
        """Request a diagnostic traceback before terminating an unready child."""
        if worker.pid is None or not hasattr(signal, "SIGUSR1"):
            return

        logger.warning(
            "Requesting traceback dump from unready worker slot %s process %s",
            index,
            worker.pid,
        )
        try:
            os.kill(worker.pid, signal.SIGUSR1)
        except ProcessLookupError:
            logger.debug(
                "Worker slot %s process %s exited before traceback dump request",
                index,
                worker.pid,
            )
            return
        except OSError as err:
            logger.warning(
                "Could not request traceback dump from worker slot %s process %s: %s",
                index,
                worker.pid,
                err,
            )
            return

        time.sleep(self.WORKER_TRACEBACK_DUMP_DELAY)

    def _start_worker(self, index: int) -> multiprocessing.Process:
        """Start a worker process and reset parent readiness for its slot."""
        worker_args, worker_kwargs = self._worker_init_args[index]
        worker = cast(
            multiprocessing.Process,
            MP_CONTEXT.Process(
                name=f"MCPClientWorker-{index}",
                target=self.worker_function,
                args=worker_args,
                kwargs=worker_kwargs,
            ),
        )
        worker.daemon = False
        worker.start()
        self.worker_started_at[index] = time.monotonic()
        self.worker_ready_at.pop(index, None)
        self.worker_ready.pop(index, None)
        self.worker_state[index] = WorkerState.STARTING
        logger.info(
            "Worker slot %s started process %s; waiting for ready message",
            index,
            worker.pid,
        )

        return worker
