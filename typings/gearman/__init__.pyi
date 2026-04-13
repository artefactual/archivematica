from collections.abc import Callable
from collections.abc import Collection
from collections.abc import Sequence
from types import TracebackType
from typing import TypedDict
from typing import overload

from .constants import _Priority
from .job import GearmanJob
from .job import GearmanJobRequest

__all__: list[str]
__version__: str

class _SSLConnectionDefinition(TypedDict):
    host: str
    port: int
    keyfile: str
    certfile: str
    ca_certs: str

class DataEncoder:
    @classmethod
    def encode(cls, encodable_object: object) -> object: ...
    @classmethod
    def decode(cls, decodable_string: object) -> object: ...

class GearmanClient:
    data_encoder: type[DataEncoder]
    connection_list: list[object]
    request_to_rotating_connection_queue: dict[GearmanJobRequest, object]

    def __init__(
        self,
        host_list: Sequence[str | tuple[str, int] | _SSLConnectionDefinition]
        | None = ...,
        random_unique_bytes: int = ...,
    ) -> None: ...
    def submit_job(
        self,
        task: str | bytes,
        data: object,
        unique: str | bytes | None = ...,
        priority: _Priority = ...,
        **kwargs: object,
    ) -> GearmanJobRequest: ...
    @overload
    def wait_until_jobs_accepted(
        self,
        job_requests: list[GearmanJobRequest],
        poll_timeout: float | None = ...,
    ) -> list[GearmanJobRequest]: ...
    @overload
    def wait_until_jobs_accepted(
        self,
        job_requests: tuple[GearmanJobRequest, ...],
        poll_timeout: float | None = ...,
    ) -> tuple[GearmanJobRequest, ...]: ...
    @overload
    def wait_until_jobs_accepted(
        self,
        job_requests: set[GearmanJobRequest],
        poll_timeout: float | None = ...,
    ) -> set[GearmanJobRequest]: ...
    def poll_connections_until_stopped(
        self,
        submitted_connections: Collection[object],
        callback_fxn: Callable[[bool], bool],
        timeout: float | None = ...,
    ) -> bool: ...
    def shutdown(self) -> None: ...

class GearmanWorker:
    data_encoder: type[DataEncoder]
    worker_client_id: str | bytes | None

    def __init__(
        self,
        host_list: Sequence[str | tuple[str, int] | _SSLConnectionDefinition]
        | None = ...,
    ) -> None: ...
    def set_client_id(self, client_id: str | bytes) -> str | bytes: ...
    def register_task(
        self,
        task: str | bytes,
        callback_function: Callable[[GearmanWorker, GearmanJob], object],
    ) -> str | bytes: ...
    def on_job_exception(
        self,
        current_job: GearmanJob,
        exc_info: tuple[type[BaseException], BaseException, TracebackType | None]
        | tuple[None, None, None],
    ) -> bool: ...
    def work(self, poll_timeout: float = ...) -> None: ...
