from typing import Literal
from typing import TypeAlias

_DEBUG_MODE_: bool
DEFAULT_GEARMAN_PORT: int

PRIORITY_NONE: None
PRIORITY_LOW: Literal["LOW"]
PRIORITY_HIGH: Literal["HIGH"]

JOB_UNKNOWN: Literal["UNKNOWN"]
JOB_PENDING: Literal["PENDING"]
JOB_CREATED: Literal["CREATED"]
JOB_FAILED: Literal["FAILED"]
JOB_COMPLETE: Literal["COMPLETE"]

_Priority: TypeAlias = None | Literal["LOW", "HIGH"]
