# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import itertools
import json

from django.core.management.base import BaseCommand
from frozendict import frozendict


class Command(BaseCommand):
    help = "Generate updates from FPR dumpdata JSON files"

    def add_arguments(self, parser):
        parser.add_argument(
            "old_json", help="Path to a JSON dump of the old/current FPR"
        )
        parser.add_argument(
            "new_json", help="Path to a JSON dump of the new/updated FPR"
        )
        parser.add_argument("output", help="Path to output file")

    def handle(self, *args, **options):
        print(args, options)
        # Load JSON
        with open(options["old_json"], "rU") as f:
            old_json = json.load(f)
        with open(options["new_json"], "rU") as f:
            new_json = json.load(f)

        # Put JSONs in a set - must freeze to be hashable
        old_json_set = set()
        for x in old_json:
            old_json_set.add(freeze(x))
        new_json_set = set()
        for x in new_json:
            new_json_set.add(freeze(x))

        # Subtract old from new
        new_entries = new_json_set - old_json_set

        # Find unversioned but updated items
        # TODO How to handle rows that have been modified in place?
        not_versioned_models = (
            "fpr.format",
            "fpr.formatgroup",
            "fpr.idtool",
            "fpr.fptool",
        )
        old_not_versioned = set(
            (x["model"], x["pk"])
            for x in old_json_set
            if x["model"] in not_versioned_models
        )
        updated_not_versioned = set(
            (x["model"], x["pk"])
            for x in new_entries
            if x["model"] in not_versioned_models
        )
        updated_pks = updated_not_versioned & old_not_versioned
        print("Items that are not versioned and were updated", updated_pks)

        # Produce JSON sorted by model & pk
        new_entries = [unfreeze(x) for x in new_entries]
        new_entries = sorted(new_entries, key=lambda x: (x["model"], x["pk"]))

        print(len(new_entries), "new entries total")
        groups = itertools.groupby(new_entries, lambda x: x["model"])
        for k, g in groups:
            print(len(list(g)), "new entries for", k)
        # Write to output file
        with open(options["output"], "w") as f:
            json.dump(new_entries, f, indent=4, separators=(",", ": "))


def freeze(item):
    item["fields"] = frozendict(item["fields"])
    return frozendict(item)


def unfreeze(item):
    item = dict(item)
    item["fields"] = dict(item["fields"])
    return item
