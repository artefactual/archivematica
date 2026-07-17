import argparse
import itertools
import json
from typing import Any

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

FPRItem = dict[str, Any]


class Command(BaseCommand):
    help = "Generate updates from FPR dumpdata JSON files"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "old_json", help="Path to a JSON dump of the old/current FPR"
        )
        parser.add_argument(
            "new_json", help="Path to a JSON dump of the new/updated FPR"
        )
        parser.add_argument("output", help="Path to output file")

    def handle(self, *args: Any, **options: Any) -> None:
        print(args, options)
        # Load JSON
        with open(options["old_json"]) as f:
            old_json: list[FPRItem] = json.load(f)
        with open(options["new_json"]) as f:
            new_json: list[FPRItem] = json.load(f)

        old_by_identity = {_identity(item): item for item in old_json}
        old_by_semantic_content = {
            _comparison_key(item, ignore_uuid=True): item for item in old_json
        }

        new_entries = []
        drifted_items = []
        drifted_uuids = set()
        for item in new_json:
            old_item = old_by_identity.get(_identity(item))
            if old_item is not None:
                if _comparison_key(old_item) == _comparison_key(item):
                    continue
                new_entries.append(item)
                continue

            old_item = old_by_semantic_content.get(
                _comparison_key(item, ignore_uuid=True)
            )
            if old_item is not None:
                old_uuid = old_item["fields"]["uuid"]
                new_uuid = item["fields"]["uuid"]
                drifted_items.append((item["model"], old_uuid, new_uuid))
                drifted_uuids.add(new_uuid)
                continue

            new_entries.append(item)

        referenced_drifted_uuids = set()
        for item in new_entries:
            referenced_drifted_uuids.update(
                _find_referenced_uuids(item["fields"], drifted_uuids)
            )
        if referenced_drifted_uuids:
            references = ", ".join(sorted(referenced_drifted_uuids))
            raise CommandError(
                "New FPR entries reference UUIDs that identify semantically "
                f"unchanged records in the old FPR: {references}"
            )

        if drifted_items:
            print("Semantically unchanged items with different UUIDs", drifted_items)

        # Find unversioned but updated items
        # TODO How to handle rows that have been modified in place?
        not_versioned_models = (
            "fpr.format",
            "fpr.formatgroup",
            "fpr.idtool",
            "fpr.fptool",
        )
        old_not_versioned = {
            (x["model"], x["pk"])
            for x in old_json
            if x["model"] in not_versioned_models
        }
        updated_not_versioned = {
            (x["model"], x["pk"])
            for x in new_entries
            if x["model"] in not_versioned_models
        }
        updated_pks = updated_not_versioned & old_not_versioned
        print("Items that are not versioned and were updated", updated_pks)

        # Produce JSON sorted by model & pk
        new_entries = sorted(new_entries, key=lambda x: (x["model"], x["pk"]))

        print(len(new_entries), "new entries total")
        groups = itertools.groupby(new_entries, lambda x: x["model"])
        for k, g in groups:
            print(len(list(g)), "new entries for", k)
        # Write to output file
        with open(options["output"], "w") as f:
            json.dump(new_entries, f, indent=4, separators=(",", ": "))


def _identity(item: FPRItem) -> tuple[str, str]:
    return item["model"], item["fields"]["uuid"]


def _comparison_key(item: FPRItem, *, ignore_uuid: bool = False) -> str:
    fields = dict(item["fields"])
    fields.pop("lastmodified", None)
    if ignore_uuid:
        fields.pop("uuid", None)
    return json.dumps(
        {"model": item["model"], "fields": fields},
        sort_keys=True,
        separators=(",", ":"),
    )


def _find_referenced_uuids(value: Any, candidates: set[str]) -> set[str]:
    if isinstance(value, dict):
        referenced = set()
        for nested_value in value.values():
            referenced.update(_find_referenced_uuids(nested_value, candidates))
        return referenced
    if isinstance(value, list):
        referenced = set()
        for nested_value in value:
            referenced.update(_find_referenced_uuids(nested_value, candidates))
        return referenced
    if isinstance(value, str) and value in candidates:
        return {value}
    return set()
