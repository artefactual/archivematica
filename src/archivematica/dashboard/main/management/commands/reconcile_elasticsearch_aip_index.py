"""Reconcile Elasticsearch AIP index location fields from Storage Service.

This command checks the AIP document in Elasticsearch against the package data
stored in the Archivematica Storage Service. It is useful after moving AIPs or
changing an AIP store path without rebuilding the entire index.

Execution examples:

./manage.py reconcile_elasticsearch_aip_index --dry-run --uuid <aip_uuid>
./manage.py reconcile_elasticsearch_aip_index --dry-run --aip-store-location <location_uuid>
./manage.py reconcile_elasticsearch_aip_index --aip-store-location <location_uuid> --pipeline <pipeline_uuid>
"""

import posixpath
import sys
import uuid as uuidlib
from dataclasses import dataclass
from typing import Any
from typing import Optional
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import CommandError

import archivematica.search.constants
from archivematica.archivematicaCommon import archivematicaFunctions as am
from archivematica.archivematicaCommon import storageService
from archivematica.dashboard.main.management.commands import DashboardCommand
from archivematica.search.service import AIPNotFoundError
from archivematica.search.service import MultipleResultsError
from archivematica.search.service import SearchServiceError
from archivematica.search.service import setup_search_service_from_conf

AIP_INDEX_FIELDS = ["filePath", "location", "origin"]
PACKAGE_TYPES_TO_RECONCILE = ("AIP", "AIC")
PACKAGE_STATUSES_TO_RECONCILE = (
    archivematica.search.constants.STATUS_UPLOADED,
    archivematica.search.constants.STATUS_DELETE_REQUESTED,
)


@dataclass(frozen=True)
class ReconciliationResult:
    uuid: str
    changes: dict[str, tuple[str, str]]
    skipped: str = ""


def _resource_uuid(resource_uri: str) -> str:
    """Return the UUID component from a Storage Service resource URI."""
    parsed_path = urlparse(resource_uri).path
    return parsed_path.rstrip("/").rsplit("/", 1)[-1]


def _validate_uuid(value: str, option: str) -> str:
    """Validate and normalize a UUID command option."""
    try:
        return str(uuidlib.UUID(value))
    except ValueError:
        raise CommandError(f"{option} must be a UUID.")


def _get_packages_in_location(location_uuid: str) -> list[dict[str, Any]]:
    """Return Storage Service packages in a current location by location UUID."""
    url = storageService._storage_service_url() + "file/"
    params: dict[str, Any] = {
        "current_location__uuid": _validate_uuid(
            location_uuid, "--aip-store-location"
        ),
        "offset": 0,
    }
    packages = []

    while True:
        with storageService.ss_api_timer(function="get_file_info"):
            response = storageService._storage_api_slow_session().get(url, params=params)
        response.raise_for_status()
        data = response.json()
        packages += data["objects"]
        if not data["meta"]["next"]:
            break
        params["offset"] += data["meta"]["limit"]

    return packages


def build_index_file_path(package: dict[str, Any], location: dict[str, Any]) -> str:
    """Build the expected AIP index filePath from Storage Service data."""
    current_full_path = package.get("current_full_path")
    if current_full_path:
        return posixpath.normpath(current_full_path)

    location_path = location.get("path")
    if not location_path:
        raise CommandError(
            f"Storage location for package {package['uuid']} does not include a path."
        )

    return posixpath.normpath(
        posixpath.join(
            location_path.rstrip("/"),
            package.get("current_path", "").lstrip("/"),
        )
    )


def expected_index_fields(package: dict[str, Any]) -> dict[str, str]:
    """Return the expected Elasticsearch fields for a Storage Service package."""
    location = storageService.location_description_from_slug(
        package["current_location"]
    )
    description = location.get("description") or location.get("path") or ""
    if not description:
        raise CommandError(
            f"Storage location for package {package['uuid']} does not include "
            "a description or path."
        )

    return {
        "filePath": build_index_file_path(package, location),
        "location": description,
        "origin": _resource_uuid(package["origin_pipeline"]),
    }


def changed_fields(
    indexed_fields: dict[str, Any],
    expected_fields: dict[str, str],
) -> dict[str, tuple[str, str]]:
    """Return changed ES fields as current and expected value tuples."""
    changes = {}
    for field, expected_value in expected_fields.items():
        current_value = indexed_fields.get(field, "")
        if current_value != expected_value:
            changes[field] = (current_value, expected_value)
    return changes


class Command(DashboardCommand):
    help = __doc__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dashboard_uuid = am.get_dashboard_uuid() or ""

    def add_arguments(self, parser):
        package_scope = parser.add_mutually_exclusive_group(required=True)
        package_scope.add_argument(
            "-u",
            "--uuid",
            help="Reconcile a single AIP/AIC by UUID.",
        )
        package_scope.add_argument(
            "--aip-store-location",
            help=(
                "Reconcile all AIPs/AICs in this AIP store location. Must be "
                "a Storage Service location UUID."
            ),
        )
        parser.add_argument(
            "--pipeline",
            default=self.dashboard_uuid,
            help=(
                "Pipeline UUID to use when reconciling all packages. Defaults "
                "to this dashboard pipeline."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print the Elasticsearch changes that would be applied.",
        )
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Refresh the AIPs index immediately after each update.",
        )

    def handle(self, *args, **options):
        if archivematica.search.constants.AIPS_INDEX not in settings.SEARCH_ENABLED:
            raise CommandError(
                "The AIPs index is not enabled. Please enable the AIPs "
                "Elasticsearch index before running this command."
            )

        try:
            search_service = setup_search_service_from_conf(settings)
        except SearchServiceError as err:
            raise CommandError(f"Unable to connect to the search service: {err}")

        packages = self._packages_to_reconcile(
            options["uuid"],
            options["aip_store_location"],
            options["pipeline"],
        )
        if not packages:
            raise CommandError("No AIPs or AICs found to reconcile.")

        results = []
        failed = []
        for package in packages:
            try:
                result = self._reconcile_package(
                    search_service,
                    package,
                    dry_run=options["dry_run"],
                    refresh=options["refresh"],
                )
            except (AIPNotFoundError, MultipleResultsError, CommandError) as err:
                failed.append(package["uuid"])
                self.error(f"{package['uuid']}: {err}")
                continue

            results.append(result)
            self._print_result(result, dry_run=options["dry_run"])

        changed = sum(1 for result in results if result.changes)
        unchanged = sum(
            1
            for result in results
            if not result.changes and not result.skipped
        )
        skipped = sum(1 for result in results if result.skipped)
        message = (
            f"Reconciliation complete. Processed {len(results)} packages: "
            f"{changed} changed, {unchanged} already matched, {skipped} skipped"
        )
        if failed:
            self.error(f"{message}, {len(failed)} failed.")
            sys.exit(1)

        self.success(f"{message}.")

    def _packages_to_reconcile(
        self,
        package_uuid: Optional[str],
        aip_store_location: Optional[str],
        pipeline_uuid: str,
    ) -> list[dict[str, Any]]:
        if package_uuid:
            return storageService.get_file_info(uuid=package_uuid)

        if not aip_store_location:
            raise CommandError("Either --uuid or --aip-store-location is required.")

        packages = _get_packages_in_location(aip_store_location)
        return storageService.filter_packages(
            packages,
            package_types=PACKAGE_TYPES_TO_RECONCILE,
            pipeline_uuid=pipeline_uuid,
            filter_replicas=True,
        )

    def _reconcile_package(
        self,
        search_service,
        package: dict[str, Any],
        dry_run: bool,
        refresh: bool,
    ) -> ReconciliationResult:
        if package.get("status") not in PACKAGE_STATUSES_TO_RECONCILE:
            return ReconciliationResult(
                uuid=package["uuid"],
                changes={},
                skipped=f"package status is {package.get('status')}",
            )

        aip = search_service.get_aip_data(package["uuid"], fields=AIP_INDEX_FIELDS)
        expected = expected_index_fields(package)
        changes = changed_fields(aip["_source"], expected)
        if dry_run:
            return ReconciliationResult(
                uuid=package["uuid"],
                changes=changes,
            )

        if changes:
            search_service.client.update(
                index=archivematica.search.constants.AIPS_INDEX,
                id=aip["_id"],
                doc={field: new for field, (_, new) in changes.items()},
                refresh=refresh,
            )
        return ReconciliationResult(
            uuid=package["uuid"],
            changes=changes,
        )

    def _print_result(self, result: ReconciliationResult, dry_run: bool) -> None:
        if result.skipped:
            self.warning(f"{result.uuid}: skipped, {result.skipped}.")
            return

        if not result.changes:
            if dry_run:
                return
            self.info(f"{result.uuid}: Elasticsearch fields already matched.")
            return

        prefix = "would update" if dry_run else "updated"
        changed = ", ".join(result.changes)
        self.info(f"{result.uuid}: {prefix} Elasticsearch fields: {changed}")
        for field, (current, expected) in result.changes.items():
            self.info(f"  {field}: {current!r} -> {expected!r}")
