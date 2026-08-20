"""Shared Gearman transport and worker-reconnection behavior.

Gearman keeps its queue in memory.  Reconnecting workers is safe because they
only advertise abilities and wait for new work.  Replaying producer requests is
not safe: a connection can disappear after gearmand accepted the request but
before the client received ``JOB_CREATED``.
"""

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional
from typing import Protocol

import gearman
from gearman.connection import GearmanConnection as BaseGearmanConnection


class ShutdownEvent(Protocol):
    def is_set(self) -> bool: ...

    def wait(self, timeout: float) -> bool: ...


class GearmanConnection(BaseGearmanConnection):
    """Gearman connection with bounded TCP attempts and liveness detection.

    python-gearman applies these options to every socket that it creates.  With
    the defaults, a silent peer should generally be detected about 90 seconds
    after the last packet on platforms supporting the Linux keepalive options.
    """

    connect_timeout = 5.0
    keepalive = True
    keepalive_idle = 60
    keepalive_interval = 10
    keepalive_count = 3


class GearmanClient(gearman.GearmanClient):
    """Gearman client using :class:`GearmanConnection` for every socket."""

    connection_class = GearmanConnection


@dataclass
class ExponentialBackoff:
    """Exponential delay with bounded proportional jitter."""

    initial_delay: float = 1.0
    maximum_delay: float = 30.0
    multiplier: float = 2.0
    jitter: float = 0.2
    random_uniform: Callable[[float, float], float] = random.uniform

    def __post_init__(self) -> None:
        self._next_delay = self.initial_delay

    def reset(self) -> None:
        self._next_delay = self.initial_delay

    def next_delay(self) -> float:
        base_delay = min(self._next_delay, self.maximum_delay)
        spread = base_delay * self.jitter
        delay = self.random_uniform(max(0.0, base_delay - spread), base_delay + spread)
        self._next_delay = min(self.maximum_delay, self._next_delay * self.multiplier)
        return min(delay, self.maximum_delay)


class GearmanWorker(gearman.GearmanWorker):
    """Gearman worker that reconnects without exiting its process."""

    connection_class = GearmanConnection

    def work_with_reconnect(
        self,
        shutdown_event: ShutdownEvent,
        logger: logging.Logger,
        *,
        poll_timeout: float = 5.0,
        stable_connection_time: float = 30.0,
        backoff: Optional[ExponentialBackoff] = None,
        monotonic: Callable[[], float] = time.monotonic,
        on_connection_unavailable: Optional[Callable[[], None]] = None,
    ) -> None:
        """Work until shutdown, retrying only expected availability failures.

        Ability and client-ID registration remain in python-gearman's handler
        initial state, so its normal ``establish_connection`` path restores
        both on each newly resolved connection.
        """
        retry_backoff = backoff or ExponentialBackoff()
        unavailable = False

        while not shutdown_event.is_set():
            worker_connections = self.establish_worker_connections()

            if worker_connections:
                connection_started = monotonic()
                if unavailable:
                    logger.info(
                        "Reconnected to Gearman; restoring worker registrations"
                    )
                    unavailable = False

                try:
                    self.work(poll_timeout=poll_timeout)
                    return
                except gearman.errors.ServerUnavailable as caught_error:
                    connection_error = caught_error
                    if monotonic() - connection_started >= stable_connection_time:
                        retry_backoff.reset()
            else:
                connection_error = gearman.errors.ServerUnavailable(
                    f"Found no valid connections in list: {self.connection_list!r}"
                )

            if not unavailable:
                logger.warning("Gearman connection unavailable: %s", connection_error)
                unavailable = True
                if on_connection_unavailable is not None:
                    on_connection_unavailable()

            if shutdown_event.wait(retry_backoff.next_delay()):
                return
