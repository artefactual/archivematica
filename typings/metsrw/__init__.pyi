from os import PathLike
from typing import IO

from lxml import etree

from . import plugins as plugins
from .plugins import premisrw

_TransformFile = dict[str, object]
_MetadataSection = object
_PremisInput = premisrw.PREMISElement | premisrw._PremisData | etree._Element

__all__: list[str]

class _DependencyPossessorMeta(type): ...

class Agent:
    role: str
    id: str | None
    type: str | None
    name: str | None
    notes: list[str]

    def __init__(
        self,
        role: str,
        **kwargs: object,
    ) -> None: ...

class AltRecordID:
    text: str
    id: str | None
    type: str | None

    def __init__(self, alt_record_id: str, **kwargs: object) -> None: ...

class FSEntry(metaclass=_DependencyPossessorMeta):
    PREMIS_OBJECT: str
    PREMIS_EVENT: str
    PREMIS_AGENT: str
    PREMIS_RIGHTS: str
    path: str | None
    type: str | None
    use: str | None
    file_uuid: str | None
    label: str | None
    checksum: str | None
    checksumtype: str | None
    parent: FSEntry | None
    derived_from: FSEntry | str | None
    transform_files: list[_TransformFile]
    amdsecs: list[_MetadataSection]
    dmdsecs: list[_MetadataSection]
    dmdsecs_by_mdtype: dict[str, list[_MetadataSection]]

    def __init__(
        self,
        path: str | bytes | None = ...,
        fileid: str | None = ...,
        label: str | None = ...,
        use: str | None = ...,
        type: str = ...,
        children: list[FSEntry] | None = ...,
        file_uuid: str | None = ...,
        derived_from: FSEntry | None = ...,
        checksum: str | None = ...,
        checksumtype: str | None = ...,
        transform_files: list[_TransformFile] | None = ...,
        mets_div_type: str | None = ...,
    ) -> None: ...
    @classmethod
    def dir(cls, label: str, children: list[FSEntry]) -> FSEntry: ...
    @property
    def children(self) -> list[FSEntry]: ...
    @property
    def is_empty_dir(self) -> bool: ...
    def file_id(self) -> str | None: ...
    def group_id(self) -> str | None: ...
    def add_child(self, child: FSEntry) -> FSEntry: ...
    def remove_child(self, child: FSEntry) -> None: ...
    def add_premis_object(
        self,
        md: _PremisInput,
        mode: str = ...,
    ) -> _MetadataSection: ...
    def add_premis_event(
        self,
        md: _PremisInput,
        mode: str = ...,
    ) -> _MetadataSection: ...
    def add_premis_agent(
        self,
        md: _PremisInput,
        mode: str = ...,
    ) -> _MetadataSection: ...
    def add_premis_rights(
        self,
        md: _PremisInput,
        mode: str = ...,
    ) -> _MetadataSection: ...
    def get_premis_objects(self) -> list[premisrw.PREMISElement]: ...

class METSDocument:
    tree: etree._ElementTree | etree._Element | None
    createdate: str | None
    objid: str | None
    agents: list[Agent]
    alternate_ids: list[AltRecordID]
    dmdsecs: list[_MetadataSection]
    amdsecs: list[_MetadataSection]

    def __init__(self) -> None: ...
    @classmethod
    def read(
        cls,
        source: str | bytes | PathLike[str] | PathLike[bytes] | IO[str] | IO[bytes],
    ) -> METSDocument: ...
    @classmethod
    def fromfile(
        cls,
        path: str | bytes | PathLike[str] | PathLike[bytes] | IO[str] | IO[bytes],
    ) -> METSDocument: ...
    @classmethod
    def fromstring(cls, string: str | bytes) -> METSDocument: ...
    @classmethod
    def fromtree(cls, tree: etree._ElementTree | etree._Element) -> METSDocument: ...
    def append_file(self, fs_entry: FSEntry) -> None: ...
    def append(self, fs_entry: FSEntry) -> None: ...
    def serialize(
        self,
        fully_qualified: bool = ...,
        normative_structmap: bool = ...,
    ) -> etree._Element: ...
    def tostring(
        self,
        fully_qualified: bool = ...,
        pretty_print: bool = ...,
        encoding: str = ...,
    ) -> str | bytes: ...
    def write(
        self,
        filepath: str | bytes | PathLike[str] | PathLike[bytes],
        fully_qualified: bool = ...,
        pretty_print: bool = ...,
        encoding: str = ...,
    ) -> None: ...
    def all_files(self) -> set[FSEntry]: ...
    def get_file(self, **kwargs: object) -> FSEntry | None: ...
