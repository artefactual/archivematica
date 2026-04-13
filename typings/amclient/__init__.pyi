from collections.abc import Mapping

from requests import Response

__all__: list[str]

class AMClient:
    reingest_type: str
    transfer_type: str
    directory: str
    output_mode: str
    package_uuid: str
    relative_path: str
    ss_api_key: str
    ss_url: str
    ss_user_name: str
    stream: bool

    def __init__(self, **kwargs: object) -> None: ...
    @staticmethod
    def version() -> str: ...
    def stdout(self, stuff: object) -> None: ...
    def download_package(self, uuid: str) -> str | None: ...
    def extract_file_stream(self) -> Response | Mapping[str, str] | None: ...
    def extract_file(self) -> Response | Mapping[str, str] | None: ...
    def __getattr__(self, name: str) -> object: ...
