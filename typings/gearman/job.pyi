from collections import deque
from typing import Any

from .constants import _Priority

class GearmanJob:
    connection: object
    handle: str | bytes | None
    task: str | bytes
    unique: str | bytes
    data: dict[str, Any]

    def __init__(
        self,
        connection: object,
        handle: str | bytes | None,
        task: str | bytes,
        unique: str | bytes,
        data: dict[str, Any],
    ) -> None: ...
    def to_dict(self) -> dict[str, object]: ...

class GearmanJobRequest:
    gearman_job: GearmanJob
    priority: _Priority
    background: bool
    connection_attempts: int
    max_connection_attempts: int
    result: object
    exception: object
    warning_updates: deque[object]
    data_updates: deque[object]
    status: dict[str, object]
    state: str
    timed_out: bool

    def __init__(
        self,
        gearman_job: GearmanJob,
        initial_priority: _Priority = ...,
        background: bool = ...,
        max_attempts: int = ...,
    ) -> None: ...
    def reset(self) -> None: ...
    @property
    def job(self) -> GearmanJob: ...
    @property
    def complete(self) -> bool: ...
