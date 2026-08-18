"""Unit tests for transfer-source path planning and materialization."""

from types import SimpleNamespace
from unittest import mock

import pytest

from archivematica.archivematicaCommon import transfer_publication
from archivematica.archivematicaCommon import transfer_source_retrieval
from archivematica.archivematicaCommon.transfer_source_retrieval import LocationPath
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    TransferSourcePathPlan,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    TransferSourceRetrievalError,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    build_transfer_source_copy_files,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    copy_transfer_source_files,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    plan_transfer_source_paths,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    retrieve_transfer_source,
)


class FakeStorageService:
    """Small Storage Service contract fake that records copy requests."""

    def __init__(self, copy_result=({"ok": True}, None)):
        self.processing_location = {
            "uuid": "processing-loc",
            "path": "%sharedPath%currentlyProcessing/",
        }
        self.transfer_sources = [
            {
                "uuid": "source-loc",
                "path": "/transfer/source",
                "resource_uri": "/api/v2/location/source-loc/",
            }
        ]
        self.default_location = {"uuid": "source-loc"}
        self.default_location_calls = []
        self.copy_result = copy_result
        self.copy_calls = []

    def get_first_location(self, purpose):
        assert purpose == "CP"
        return self.processing_location

    def get_location(self, purpose):
        assert purpose == "TS"
        return self.transfer_sources

    def get_default_location(self, purpose):
        assert purpose == "TS"
        self.default_location_calls.append(purpose)
        return self.default_location

    def copy_files(self, source_location, destination_location, files):
        self.copy_calls.append((source_location, destination_location, files))
        return self.copy_result


@pytest.fixture
def retrieval_paths(tmp_path):
    """Create the staging and processing layout used by retrieval helpers."""
    shared = tmp_path / "sharedDirectory"
    processing = shared / "currentlyProcessing"
    copied = shared / "tmp" / "tmp123" / "transfer"
    copied.mkdir(parents=True)
    processing.mkdir()

    return SimpleNamespace(shared=shared, processing=processing, copied=copied)


@pytest.mark.parametrize(
    "path,expected",
    [
        ("location-uuid:/var/source/path", ("location-uuid", "/var/source/path")),
        ("/var/source/path", (None, "/var/source/path")),
    ],
)
def test_location_path_parts(path, expected):
    assert LocationPath(path).parts() == expected


@pytest.mark.parametrize(
    "name",
    [
        "DESTINATION_REFRESH_PREFIX",
        "TransferSourceRetrievalError",
        "TransferSourceRetrievalResult",
        "check_retrieved_path_exists",
        "is_destination_refresh_name",
        "move_to_internal_shared_dir",
        "pad_destination_path_if_it_already_exists",
    ],
)
def test_publication_api_remains_reexported(name):
    assert getattr(transfer_source_retrieval, name) is getattr(
        transfer_publication, name
    )


@pytest.mark.parametrize(
    "name,path,tmpdir,shared_directory,expected",
    [
        (
            "TransferName",
            "location-uuid:home/username/archive.zip",
            "/var/archivematica/sharedDirectory/tmp/tmp123",
            "/var/archivematica/sharedDirectory/",
            TransferSourcePathPlan(
                copy_destination_relative="tmp/tmp123",
                copied_path="/var/archivematica/sharedDirectory/tmp/tmp123/archive.zip",
                copy_source="location-uuid:home/username/archive.zip",
            ),
        ),
        (
            "TransferName",
            "location-uuid:home/username/dir",
            "/var/archivematica/sharedDirectory/tmp/tmp456",
            "/var/archivematica/sharedDirectory/",
            TransferSourcePathPlan(
                copy_destination_relative="tmp/tmp456/TransferName",
                copied_path="/var/archivematica/sharedDirectory/tmp/tmp456/TransferName",
                copy_source="location-uuid:home/username/dir/.",
            ),
        ),
    ],
)
def test_plan_transfer_source_paths(name, path, tmpdir, shared_directory, expected):
    plan = plan_transfer_source_paths(name, path, tmpdir, shared_directory)

    assert plan == expected


def test_plan_transfer_source_paths_rejects_reserved_destination_name():
    marker = (
        f"{transfer_source_retrieval.DESTINATION_REFRESH_PREFIX}"
        f"{'0123456789abcdef' * 2}"
    )

    with pytest.raises(TransferSourceRetrievalError, match="is reserved"):
        plan_transfer_source_paths(
            marker,
            "location-uuid:home/username/dir",
            "/var/archivematica/sharedDirectory/tmp/tmp123",
            "/var/archivematica/sharedDirectory/",
        )


def test_build_transfer_source_copy_files_groups_files_by_location():
    processing_location = {"path": "%sharedPath%currentlyProcessing/"}
    transfer_sources = [
        {"uuid": "loc-1", "path": "/transfer/source/one"},
        {"uuid": "loc-2", "path": "/transfer/source/two"},
    ]

    result = build_transfer_source_copy_files(
        [
            "loc-1:/transfer/source/one/path/to/file.txt",
            "loc-2:/transfer/source/two/path/to/directory/",
        ],
        "tmp/tmp123",
        processing_location,
        transfer_sources,
    )

    assert result == {
        "loc-1": {
            "location": transfer_sources[0],
            "files": [
                {
                    "source": "path/to/file.txt",
                    "destination": "currentlyProcessing/tmp/tmp123/file.txt",
                }
            ],
        },
        "loc-2": {
            "location": transfer_sources[1],
            "files": [
                {
                    "source": "path/to/directory/",
                    "destination": "currentlyProcessing/tmp/tmp123/directory/",
                }
            ],
        },
    }


def test_build_transfer_source_copy_files_uses_default_location():
    processing_location = {"path": "%sharedPath%currentlyProcessing/"}
    transfer_sources = [{"uuid": "default-loc", "path": "/transfer/source"}]

    result = build_transfer_source_copy_files(
        ["/transfer/source/path/to/file.txt"],
        "tmp/tmp123",
        processing_location,
        transfer_sources,
        default_location_uuid="default-loc",
    )

    assert result["default-loc"]["files"] == [
        {
            "source": "path/to/file.txt",
            "destination": "currentlyProcessing/tmp/tmp123/file.txt",
        }
    ]


def test_build_transfer_source_copy_files_resolves_default_location_lazily():
    default_location_uuid_factory = mock.Mock(return_value="default-loc")
    processing_location = {"path": "%sharedPath%currentlyProcessing/"}
    transfer_sources = [{"uuid": "default-loc", "path": "/transfer/source"}]

    with pytest.raises(ValueError, match="not associated with this pipeline"):
        build_transfer_source_copy_files(
            [
                "unknown:/transfer/source/path/to/file.txt",
                "/transfer/source/path/to/other.txt",
            ],
            "tmp/tmp123",
            processing_location,
            transfer_sources,
            default_location_uuid_factory=default_location_uuid_factory,
        )

    default_location_uuid_factory.assert_not_called()


def test_build_transfer_source_copy_files_rejects_unknown_location():
    with pytest.raises(ValueError, match="not associated with this pipeline"):
        build_transfer_source_copy_files(
            ["unknown:/transfer/source/path/to/file.txt"],
            "tmp/tmp123",
            {"path": "%sharedPath%currentlyProcessing/"},
            [{"uuid": "known", "path": "/transfer/source"}],
        )


def test_copy_transfer_source_files_copies_from_storage_service():
    storage_service = FakeStorageService()

    copy_transfer_source_files(
        ["source-loc:/transfer/source/path/."],
        "tmp/tmp123/transfer",
        storage_service,
    )

    assert storage_service.copy_calls == [
        (
            storage_service.transfer_sources[0],
            storage_service.processing_location,
            [
                {
                    "source": "path/.",
                    "destination": "currentlyProcessing/tmp/tmp123/transfer/.",
                }
            ],
        )
    ]


def test_copy_transfer_source_files_resolves_unprefixed_default_location():
    """Unqualified legacy paths must still use the pipeline's default source."""
    storage_service = FakeStorageService()

    copy_transfer_source_files(
        ["/transfer/source/path/."],
        "tmp/tmp123/transfer",
        storage_service,
    )

    assert storage_service.default_location_calls == ["TS"]
    assert storage_service.copy_calls[0][2] == [
        {
            "source": "path/.",
            "destination": "currentlyProcessing/tmp/tmp123/transfer/.",
        }
    ]


def test_copy_transfer_source_files_reports_storage_service_failures():
    storage_service = FakeStorageService(copy_result=(None, TimeoutError("slow copy")))

    with pytest.raises(TransferSourceRetrievalError, match="slow copy"):
        copy_transfer_source_files(
            ["source-loc:/transfer/source/path/."],
            "tmp/tmp123/transfer",
            storage_service,
        )


def test_retrieve_transfer_source_copies_then_moves(retrieval_paths):
    storage_service = FakeStorageService()

    result = retrieve_transfer_source(
        ["source-loc:/transfer/source/path/."],
        "tmp/tmp123/transfer",
        retrieval_paths.copied,
        retrieval_paths.processing,
        f"{retrieval_paths.shared}/",
        storage_service,
    )

    assert result.final_path == (retrieval_paths.processing / "transfer").as_posix()
    assert result.current_location == "%sharedPath%currentlyProcessing/transfer"
    assert storage_service.copy_calls == [
        (
            storage_service.transfer_sources[0],
            storage_service.processing_location,
            [
                {
                    "source": "path/.",
                    "destination": "currentlyProcessing/tmp/tmp123/transfer/.",
                }
            ],
        )
    ]


def test_retrieve_transfer_source_does_not_move_when_copy_fails(retrieval_paths):
    storage_service = FakeStorageService(copy_result=(None, TimeoutError("slow copy")))

    with pytest.raises(TransferSourceRetrievalError, match="slow copy"):
        retrieve_transfer_source(
            ["source-loc:/transfer/source/path/."],
            "tmp/tmp123/transfer",
            retrieval_paths.copied,
            retrieval_paths.processing,
            f"{retrieval_paths.shared}/",
            storage_service,
        )

    assert retrieval_paths.copied.exists()
    assert not (retrieval_paths.processing / "transfer").exists()
