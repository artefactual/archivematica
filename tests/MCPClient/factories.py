"""Factories of the objects of the MCPClient tests."""

from collections.abc import Sequence

from archivematica.MCPClient.client.job import Job


class MCPJobFactory:
    """Creates client jobs, which run a client script with their arguments."""

    def __call__(
        self, arguments: Sequence[str] = (), *, name: str = "stub", uuid: str = "stub"
    ) -> Job:
        return Job(name, uuid, list(arguments))
