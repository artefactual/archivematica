from abc import ABC
from typing import Literal
from typing import TypeAlias
from typing import overload

from lxml import etree

_PremisAttributeMap: TypeAlias = dict[str, str]
_PremisValue: TypeAlias = str | _PremisAttributeMap | "_PremisData"
_PremisData: TypeAlias = tuple[_PremisValue, ...]

PREMIS_META: dict[str, str]
PREMIS_2_1_META: dict[str, str]
PREMIS_2_1_NAMESPACE: str
PREMIS_2_1_NAMESPACES: dict[str, str]
PREMIS_2_1_SCHEMA_LOCATION: str
PREMIS_2_1_VERSION: str
PREMIS_2_1_XSD: str
PREMIS_2_2_META: dict[str, str]
PREMIS_2_2_NAMESPACE: str
PREMIS_2_2_NAMESPACES: dict[str, str]
PREMIS_2_2_SCHEMA_LOCATION: str
PREMIS_2_2_VERSION: str
PREMIS_2_2_XSD: str
PREMIS_3_0_META: dict[str, str]
PREMIS_3_0_NAMESPACE: str
PREMIS_3_0_NAMESPACES: dict[str, str]
PREMIS_3_0_SCHEMA_LOCATION: str
PREMIS_3_0_VERSION: str
PREMIS_3_0_XSD: str
PREMIS_SCHEMA_LOCATION: str
PREMIS_VERSION: str
PREMIS_VERSIONS_MAP: dict[str, dict[str, dict[str, str]]]
NAMESPACES: dict[str, str]
XSI_NAMESPACE: str
__all__: list[str]

class PREMISElement(ABC):
    premis_version: str

    def __init__(self, **kwargs: object) -> None: ...
    @classmethod
    def fromtree(cls, tree: etree._Element) -> PREMISElement: ...
    @property
    def data(self) -> _PremisData: ...
    def serialize(self) -> etree._Element: ...
    def tostring(self, pretty_print: bool = ..., encoding: str = ...) -> bytes: ...
    def find(self, path: str) -> _PremisData | None: ...
    def findall(self, path: str) -> tuple[PREMISElement, ...] | None: ...
    def findtext(self, path: str) -> str | None: ...
    def find_text_or_all(self, path: str) -> str | tuple[PREMISElement, ...] | None: ...
    def __getattr__(self, name: str) -> str | tuple[PREMISElement, ...] | None: ...

class PREMISObject(PREMISElement): ...
class PREMISEvent(PREMISElement): ...
class PREMISAgent(PREMISElement): ...
class PREMISRights(PREMISElement): ...

def premis_to_data(premis_lxml_el: etree._Element) -> _PremisData: ...
def data_to_premis(data: _PremisData, premis_version: str = ...) -> etree._Element: ...
def data_find(data: _PremisData, path: str) -> _PremisData | None: ...
@overload
def data_find_all(
    data: _PremisData,
    path: str,
    dyn_cls: Literal[False] = ...,
) -> tuple[_PremisData, ...] | None: ...
@overload
def data_find_all(
    data: _PremisData,
    path: str,
    dyn_cls: Literal[True],
) -> tuple[PREMISElement, ...] | None: ...
def data_find_text(data: _PremisData, path: str) -> str | None: ...
@overload
def data_find_text_or_all(
    data: _PremisData,
    path: str,
    dyn_cls: Literal[False] = ...,
) -> str | tuple[_PremisData, ...] | None: ...
@overload
def data_find_text_or_all(
    data: _PremisData,
    path: str,
    dyn_cls: Literal[True],
) -> str | tuple[PREMISElement, ...] | None: ...
def lxmlns(arg: str | None, premis_version: str = ...) -> str: ...
def snake_to_camel_cap(snake: str) -> str: ...
def snake_to_camel(snake: str) -> str: ...
def camel_to_snake(camel: str) -> str: ...
