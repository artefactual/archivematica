from enum import IntEnum
from os import PathLike
from typing import NamedTuple

class Event(NamedTuple):
    wd: int
    mask: int
    cookie: int
    name: str

class INotify:
    @property
    def fd(self) -> int: ...
    def __init__(
        self,
        inheritable: bool = ...,
        nonblocking: bool = ...,
        closefd: bool = ...,
    ) -> None: ...
    def add_watch(
        self, path: str | bytes | PathLike[str] | PathLike[bytes], mask: int
    ) -> int: ...
    def read(
        self, timeout: int | None = ..., read_delay: int | None = ...
    ) -> list[Event]: ...
    def rm_watch(self, wd: int) -> None: ...
    def close(self) -> None: ...

def parse_events(data: bytes) -> list[Event]: ...

class flags(IntEnum):
    ACCESS = 0x00000001
    MODIFY = 0x00000002
    ATTRIB = 0x00000004
    CREATE = 0x00000100
    DELETE = 0x00000200
    CLOSE_WRITE = 0x00000008
    CLOSE_NOWRITE = 0x00000010
    OPEN = 0x00000020
    MOVED_FROM = 0x00000040
    MOVED_TO = 0x00000080
    DELETE_SELF = 0x00000400
    MOVE_SELF = 0x00000800
    UNMOUNT = 0x00002000
    Q_OVERFLOW = 0x00004000
    IGNORED = 0x00008000
    ONLYDIR = 0x01000000
    DONT_FOLLOW = 0x02000000
    EXCL_UNLINK = 0x04000000
    MASK_ADD = 0x20000000
    ISDIR = 0x40000000
    ONESHOT = 0x80000000
    @classmethod
    def from_mask(cls, mask: int) -> list[flags]: ...

class masks(IntEnum):
    CLOSE = 0x00000018
    MOVE = 0x000000C0
    ALL_EVENTS = 0x00000FFF
