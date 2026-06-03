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

from django.conf import settings
from django.core.management.base import CommandError

import archivematicaFunctions as am
import elasticSearchFunctions as es
import storageService
from main.management.commands import DashboardCommand
from main.management.commands import setup_es_for_aip_reindexing

PACKAGE_TYPES_TO_RECONCILE = ("AIP", "AIC")
PACKAGE_STATUSES_TO_RECONCILE = (es.STATUS_UPLOADED, es.STATUS_DELETE_REQUESTED)


@dataclass(frozen=True)
class ReconciliationResult:
    uuid: str
    changes: dict[str, tuple[str, str]]
    skipped: str = ""


def _resource_uuid(resource_uri: str) -> str:
    """Return the UUID component from a Storage Service resource URI."""
    return resource_uri.rstrip("/").rsplit("/", 1)[-1]


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
    packages: list[dict[str, Any]] = []

    while True:
        with storageService.ss_api_timer(function="get_file_info"):
            response = storageService._storage_api_slow_session().get(url, params=params)
        response.raise_for_status()
        data = response.json()
        packages.extend(data["objects"])
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


def _get_aip_document(es_client, package_uuid: str) -> dict[str, Any]:
    """Return the single AIP document for a package UUID."""
    results = es.search_all_results(
        es_client,
        body={"query": {"term": {es.ES_FIELD_UUID: package_uuid}}},
        index=es.AIPS_INDEX,
    )
    hits = results["hits"]["hits"]
    if not hits:
        raise CommandError(f"Unable to find AIP document for UUID {package_uuid}.")
    if len(hits) > 1:
        raise CommandError(
            f"Multiple AIP documents found for UUID {package_uuid}; unable to reconcile."
        )
    return hits[0]


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
        if es.AIPS_INDEX not in settings.SEARCH_ENABLED:
            raise CommandError(
                "The AIPs index is not enabled. Please enable the AIPs "
                "Elasticsearch index before running this command."
            )

        try:
            es_client = setup_es_for_aip_reindexing(self)
        except Exception as err:
            raise CommandError(f"Unable to connect to Elasticsearch: {err}")

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
                    es_client,
                    package,
                    dry_run=options["dry_run"],
                    refresh=options["refresh"],
                )
            except CommandError as err:
                failed.append(package["uuid"])
                self.error(f"{package['uuid']}: {err}")
                continue

            results.append(result)
            self._print_result(result, dry_run=options["dry_run"])

        changed = sum(1 for result in results if result.changes)
        unchanged = sum(1 for result in results if not result.changes and not result.skipped)
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
            package = storageService.get_file_info(uuid=_validate_uuid(package_uuid, "--uuid"))
            return package if isinstance(package, list) else [package]

        if aip_store_location:
            packages = _get_packages_in_location(aip_store_location)
        else:
            packages = storageService.get_file_info()
            packages = storageService.filter_packages(
                packages,
                package_types=PACKAGE_TYPES_TO_RECONCILE,
                statuses=PACKAGE_STATUSES_TO_RECONCILE,
                pipeline_uuid=pipeline_uuid,
                filter_replicas=True,
            )

        return [
            package
            for package in packages
            if package.get("package_type") in PACKAGE_TYPES_TO_RECONCILE
        ]

    def _reconcile_package(
        self,
        es_client,
        package: dict[str, Any],
        dry_run: bool = False,
        refresh: bool = False,
    ) -> ReconciliationResult:
        expected = expected_index_fields(package)
        indexed = _get_aip_document(es_client, package["uuid"])
        source = indexed.get("_source", {})
        changes = changed_fields(source, expected)

        if not changes:
            return ReconciliationResult(uuid=package["uuid"], changes={})

        if dry_run:
            return ReconciliationResult(uuid=package["uuid"], changes=changes)

        body = {"doc": expected}
        es_client.update(
            body=body,
            index=es.AIPS_INDEX,
            doc_type=es.DOC_TYPE,
            id=indexed["_id"],
            refresh="wait_for" if refresh else False,
        )
        return ReconciliationResult(uuid=package["uuid"], changes=changes)

    def _print_result(self, result: ReconciliationResult, dry_run: bool = False):
        if result.skipped:
            self.warning(f"{result.uuid}: skipped ({result.skipped})")
            return

        if not result.changes:
            self.info(f"{result.uuid}: already matched")
            return

        action = "would update" if dry_run else "updated"
        details = ", ".join(
            f"{field}={current!r} -> {expected!r}"
            for field, (current, expected) in sorted(result.changes.items())
        )
        self.info(f"{result.uuid}: {action} {details}")
