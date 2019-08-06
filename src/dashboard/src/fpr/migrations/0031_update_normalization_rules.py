# -*- coding: utf-8 -*-
"""Remove normalization for preservation rules for all video files
and for some common image formats."""
from __future__ import absolute_import, unicode_literals

from django.db import migrations

NORMALIZE_TO_MKV_FOR_PRES_COMMANDS = (
    "ff6d1894-1798-4b47-9408-79200052810f",
    "35334ee7-5392-4356-af48-1db7d4e95748",
    "4c915b98-3a45-4185-920e-9f9121b2ad7c",
    "0ec74b7f-a804-4184-af84-2a73c026abe8",
    "ce35f131-43b4-4ab1-85fd-282df96468f2",
    "e99b264a-c4b1-4a8f-a325-988d63c603ae",
    "b09455e8-4e00-4845-8943-a4f5d474b356",
    "fdcead79-a9e5-4b80-8a89-a863503d589d",
    "3cc88211-4275-4cca-ad53-146d526c9a70",
    "aee60620-012a-442b-a811-7bf02cebe532",
    "9db05d68-36bf-4bb2-b622-ba1563511bff",
    "1db717f6-8e14-452e-9227-2b34a497e96f",
    "703955f0-5fad-43ba-95eb-ba2902c9a0c6",
    "4d261781-ecfc-49dd-a5fe-a6098833cd48",
    "20c58ba8-610b-4877-ad98-3fcc877d0bd9",
    "a78af58d-08a4-4e1a-8325-4c616541c1e0",
    "441d57a8-1dfb-438b-9c20-7493cc7dea74",
    "80a4a7d8-8960-4be9-851f-8a1d76f6ef64",
    "aae4f3f1-83a8-4427-9385-493d46c67f2d",
    "d3c1b19c-030c-44c6-bef7-f7302b6fa282",
    "11999be6-ab40-4ff2-94ad-69d7fbcd2d52",
    "e81820ac-f992-429d-85e0-fa959d31ec54",
    "46b397a9-6dc5-4deb-b8ad-3e91fe0f9189",
    "875327b1-7d62-458f-a8a5-f44e8c38d369",
    "5458651b-6198-468c-8968-c7b3a2fb0d5e",
    "52db06e9-ed12-4ca3-83e6-6e867a171dba",
)

NORMALIZE_TO_TIFF_FOR_PRES_COMMANDS = (
    # PNG
    "a83950ae-9700-477d-a33a-a13198045562",
    "07bad3db-984d-426f-ad66-87c01bbcab94",
    "f0dfbe3e-c5f8-4425-8079-83444349d8f7",
    "90e6402f-53aa-4ba3-b8d0-118b36a456f9",
    # GIF
    "d766088f-1326-4060-9bce-7227ff2da3df",
    "70d55c10-6a7f-4b93-9f5f-bc39f5443e2a",
    "5e8a4d09-884f-4774-9a35-d40bbf28f3b9",
    # JPEG
    "371f73f5-3e87-440d-acef-253a16834da5",
    "8c1524d3-1a4c-4921-a5ef-7f95fb60d771",
    "4e2c6fac-991e-4565-a173-5a44edd5a311",
    "b1237562-04b6-4e8f-94a9-a63d040b2462",
    "c7cedd09-2bcd-434d-9c6f-1b221d40e889",
    # DNG
    "f60d15e1-4bbc-472c-acd7-859ac74cbdeb",
    "77ac41e2-db5b-4a6f-98ec-fc150e0cc7f4",
    "b6578aed-5749-491c-9be0-fdad67d5775e",
    "6816de5d-b4b5-4a29-a419-80a766e61e7d",
    "49f0fa36-a644-4c4b-bf42-7f74e749ce75",
)


def data_migration_up(apps, schema_editor):
    """De-activate normalization rules"""
    FPRule = apps.get_model("fpr", "FPRule")

    # Remove video preservation rule and any associated commands
    FPRule.objects.filter(uuid__in=NORMALIZE_TO_MKV_FOR_PRES_COMMANDS).update(
        enabled=False
    )
    # Remove preservation to TIFF commands for common images
    FPRule.objects.filter(uuid__in=NORMALIZE_TO_TIFF_FOR_PRES_COMMANDS).update(
        enabled=False
    )


def data_migration_down(apps, schema_editor):
    """Re-activate normalization rules"""
    FPRule = apps.get_model("fpr", "FPRule")

    # Bring back video preservation rule and any associated commands
    FPRule.objects.filter(uuid__in=NORMALIZE_TO_MKV_FOR_PRES_COMMANDS).update(
        enabled=True
    )
    # Bring back preservation to TIFF commands for common images
    FPRule.objects.filter(uuid__in=NORMALIZE_TO_TIFF_FOR_PRES_COMMANDS).update(
        enabled=True
    )


class Migration(migrations.Migration):

    dependencies = [("fpr", "0030_update_jhove_command")]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
