from collections.abc import Iterable

from prometheus_client.metrics_core import Metric
from prometheus_client.registry import CollectorRegistry

class MultiProcessCollector:
    def __init__(
        self,
        registry: CollectorRegistry | None,
        path: str | None = ...,
    ) -> None: ...
    @staticmethod
    def merge(
        files: Iterable[str],
        accumulate: bool = ...,
    ) -> Iterable[Metric]: ...
    def collect(self) -> Iterable[Metric]: ...

def mark_process_dead(pid: int | None, path: str | None = ...) -> None: ...
