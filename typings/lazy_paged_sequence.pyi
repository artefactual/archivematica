from collections.abc import Callable
from collections.abc import Sequence
from typing import TypeVar
from typing import overload

_T = TypeVar("_T")

class LazyPagedSequence(Sequence[_T]):
    def __init__(
        self,
        page_func: Callable[[int, int], Sequence[_T]],
        page_size: int,
        length: int,
    ) -> None: ...
    @overload
    def __getitem__(self, index: int) -> _T: ...
    @overload
    def __getitem__(self, index: slice) -> list[_T]: ...
    def __len__(self) -> int: ...
