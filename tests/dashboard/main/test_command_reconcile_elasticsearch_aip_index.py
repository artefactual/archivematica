from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError

import archivematica.search.constants
from archivematica.dashboard.main.management.commands import (
    reconcile_elasticsearch_aip_index,
)
from archivematica.search.service import SearchService


def package(**overrides):
    data = {
        "uuid": "2faa61dc-ed33-49f4-8b36-954f203bab4a",
        "status": "UPLOADED",
        "package_type": "AIP",
        "current_location": "/api/v2/location/location-uuid/",
        "current_path": "tree/a/example.7z",
        "current_full_path": "/mnt/target/tree/a/example.7z",
        "origin_pipeline": "/api/v2/pipeline/pipeline-uuid/",
        "replicated_package": None,
    }
    data.update(overrides)
    return data


def test_expected_index_fields_uses_storage_service_location():
    pkg = package()

    with mock.patch.object(
        reconcile_elasticsearch_aip_index.storageService,
        "location_description_from_slug",
        return_value={"description": "Target AIP Store", "path": "/mnt/target"},
    ):
        fields = reconcile_elasticsearch_aip_index.expected_index_fields(pkg)

    assert fields == {
        "filePath": "/mnt/target/tree/a/example.7z",
        "location": "Target AIP Store",
        "origin": "pipeline-uuid",
    }


def test_expected_index_fields_builds_path_when_current_full_path_missing():
    pkg = package(current_full_path="")

    with mock.patch.object(
        reconcile_elasticsearch_aip_index.storageService,
        "location_description_from_slug",
        return_value={"description": "Target AIP Store", "path": "/mnt/target"},
    ):
        fields = reconcile_elasticsearch_aip_index.expected_index_fields(pkg)

    assert fields["filePath"] == "/mnt/target/tree/a/example.7z"


def test_changed_fields_reports_only_differences():
    changes = reconcile_elasticsearch_aip_index.changed_fields(
        {
            "filePath": "/mnt/source/tree/a/example.7z",
            "location": "Target AIP Store",
            "origin": "pipeline-uuid",
        },
        {
            "filePath": "/mnt/target/tree/a/example.7z",
            "location": "Target AIP Store",
            "origin": "pipeline-uuid",
        },
    )

    assert changes == {
        "filePath": ("/mnt/source/tree/a/example.7z", "/mnt/target/tree/a/example.7z")
    }


def test_validate_uuid_accepts_uuid():
    assert reconcile_elasticsearch_aip_index._validate_uuid(
        "d24839c0-c1c7-41d0-ba63-550356fbbba1", "--aip-store-location"
    ) == "d24839c0-c1c7-41d0-ba63-550356fbbba1"


def test_validate_uuid_rejects_resource_uri():
    try:
        reconcile_elasticsearch_aip_index._validate_uuid(
            "/api/v2/location/d24839c0-c1c7-41d0-ba63-550356fbbba1/",
            "--aip-store-location",
        )
    except CommandError as err:
        assert "--aip-store-location must be a UUID" in str(err)
    else:
        raise AssertionError("Expected CommandError")


def test_get_packages_in_location_uses_current_location_uuid_filter():
    response = mock.Mock()
    response.json.return_value = {
        "objects": [package()],
        "meta": {"next": None, "limit": 20},
    }
    session = mock.Mock()
    session.get.return_value = response

    with mock.patch.object(
        reconcile_elasticsearch_aip_index.storageService,
        "_storage_service_url",
        return_value="http://storage.example/api/v2/",
    ):
        with mock.patch.object(
            reconcile_elasticsearch_aip_index.storageService,
            "_storage_api_slow_session",
            return_value=session,
        ):
            packages = reconcile_elasticsearch_aip_index._get_packages_in_location(
                "d24839c0-c1c7-41d0-ba63-550356fbbba1"
            )

    assert packages == [package()]
    response.raise_for_status.assert_called_once_with()
    session.get.assert_called_once_with(
        "http://storage.example/api/v2/file/",
        params={
            "current_location__uuid": "d24839c0-c1c7-41d0-ba63-550356fbbba1",
            "offset": 0,
        },
    )


def test_packages_to_reconcile_uses_uuid_by_default():
    command = reconcile_elasticsearch_aip_index.Command()

    with mock.patch.object(
        reconcile_elasticsearch_aip_index.storageService,
        "get_file_info",
        return_value=[package()],
    ) as get_file_info:
        packages = command._packages_to_reconcile(
            "2faa61dc-ed33-49f4-8b36-954f203bab4a",
            None,
            "pipeline-uuid",
        )

    assert packages == [package()]
    get_file_info.assert_called_once_with(
        uuid="2faa61dc-ed33-49f4-8b36-954f203bab4a"
    )


def test_packages_to_reconcile_can_use_aip_store_location():
    command = reconcile_elasticsearch_aip_index.Command()
    packages = [package(), package(uuid="daa05a8c-ec53-4c27-968a-6e6bdba905ce")]
    filtered_packages = [packages[0]]

    with mock.patch.object(
        reconcile_elasticsearch_aip_index,
        "_get_packages_in_location",
        return_value=packages,
    ) as get_packages_in_location:
        with mock.patch.object(
            reconcile_elasticsearch_aip_index.storageService,
            "filter_packages",
            return_value=filtered_packages,
        ) as filter_packages:
            result = command._packages_to_reconcile(
                None,
                "d24839c0-c1c7-41d0-ba63-550356fbbba1",
                "pipeline-uuid",
            )

    assert result == filtered_packages
    get_packages_in_location.assert_called_once_with(
        "d24839c0-c1c7-41d0-ba63-550356fbbba1"
    )
    filter_packages.assert_called_once_with(
        packages,
        package_types=reconcile_elasticsearch_aip_index.PACKAGE_TYPES_TO_RECONCILE,
        pipeline_uuid="pipeline-uuid",
        filter_replicas=True,
    )


def test_command_dry_run_does_not_update(settings, capsys):
    settings.SEARCH_ENABLED = [archivematica.search.constants.AIPS_INDEX]
    search_service = mock.Mock(spec=SearchService)
    search_service.get_aip_data.return_value = {
        "_id": "document-id",
        "_source": {
            "filePath": "/mnt/source/tree/a/example.7z",
            "location": "Source AIP Store",
            "origin": "pipeline-uuid",
        },
    }

    with mock.patch.object(
        reconcile_elasticsearch_aip_index,
        "setup_search_service_from_conf",
        return_value=search_service,
    ):
        with mock.patch.object(
            reconcile_elasticsearch_aip_index.storageService,
            "get_file_info",
            return_value=[package()],
        ):
            with mock.patch.object(
                reconcile_elasticsearch_aip_index.storageService,
                "location_description_from_slug",
                return_value={
                    "description": "Target AIP Store",
                    "path": "/mnt/target",
                },
            ):
                call_command(
                    "reconcile_elasticsearch_aip_index",
                    "--dry-run",
                    "--uuid",
                    "2faa61dc-ed33-49f4-8b36-954f203bab4a",
                )

    search_service.update_aip_fields.assert_not_called()
    captured = capsys.readouterr()
    assert "would update Elasticsearch fields: filePath, location" in captured.out


def test_command_updates_changed_fields(settings):
    settings.SEARCH_ENABLED = [archivematica.search.constants.AIPS_INDEX]
    search_service = mock.Mock(spec=SearchService)
    search_service.get_aip_data.return_value = {
        "_id": "document-id",
        "_source": {
            "filePath": "/mnt/source/tree/a/example.7z",
            "location": "Source AIP Store",
            "origin": "pipeline-uuid",
        },
    }

    with mock.patch.object(
        reconcile_elasticsearch_aip_index,
        "setup_search_service_from_conf",
        return_value=search_service,
    ):
        with mock.patch.object(
            reconcile_elasticsearch_aip_index.storageService,
            "get_file_info",
            return_value=[package()],
        ):
            with mock.patch.object(
                reconcile_elasticsearch_aip_index.storageService,
                "location_description_from_slug",
                return_value={
                    "description": "Target AIP Store",
                    "path": "/mnt/target",
                },
            ):
                call_command(
                    "reconcile_elasticsearch_aip_index",
                    "--uuid",
                    "2faa61dc-ed33-49f4-8b36-954f203bab4a",
                )

    search_service.update_aip_fields.assert_called_once_with(
        "document-id",
        {
            "filePath": "/mnt/target/tree/a/example.7z",
            "location": "Target AIP Store",
        },
        refresh=False,
    )


def test_command_requires_aips_index(settings):
    settings.SEARCH_ENABLED = []

    try:
        call_command(
            "reconcile_elasticsearch_aip_index",
            "--dry-run",
            "--uuid",
            "2faa61dc-ed33-49f4-8b36-954f203bab4a",
        )
    except CommandError as err:
        assert "AIPs index is not enabled" in str(err)
    else:
        raise AssertionError("Expected CommandError")
