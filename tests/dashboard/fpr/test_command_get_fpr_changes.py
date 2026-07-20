import json
import pathlib

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


def test_command_outputs_new_fpr_entries(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    old_json = [
        {
            "model": "fpr.formatgroup",
            "pk": 1,
            "fields": {
                "uuid": "c94ce0e6-c275-4c09-b802-695a18b7bf2a",
                "description": "Audio",
                "slug": "audio",
            },
        },
        {
            "model": "fpr.format",
            "pk": 1,
            "fields": {
                "uuid": "22147b00-0fdc-4653-aa7b-618d1f4b6ffb",
                "description": "Audio Interchange File Format",
                "group": "c94ce0e6-c275-4c09-b802-695a18b7bf2a",
                "slug": "audio-interchange-file-format",
            },
        },
        {
            "model": "fpr.formatversion",
            "pk": 152,
            "fields": {
                "replaces": None,
                "enabled": True,
                "lastmodified": "2013-11-15T01:18:31Z",
                "uuid": "36800d63-1bb5-4324-ba8c-90e222eeddbc",
                "format": "22147b00-0fdc-4653-aa7b-618d1f4b6ffb",
                "version": "1.2",
                "pronom_id": "fmt/414",
                "description": "Audio Interchange File Format ",
                "access_format": False,
                "preservation_format": False,
                "slug": "audio-interchange-file-format-12",
            },
        },
    ]
    new_format_groups = [
        {
            "model": "fpr.formatgroup",
            "pk": 2,
            "fields": {
                "uuid": "5b14d57c-d6f1-4807-b98d-0a574d6bf8fc",
                "description": "Email",
                "slug": "email",
            },
        },
    ]
    new_formats = [
        {
            "model": "fpr.format",
            "pk": 6,
            "fields": {
                "uuid": "187d9216-7a53-4ef6-b9dd-4a397c414543",
                "description": "Archivematica Maildir",
                "group": "5b14d57c-d6f1-4807-b98d-0a574d6bf8fc",
                "slug": "archivematica-maildir",
            },
        },
    ]
    new_format_versions = [
        {
            "model": "fpr.formatversion",
            "pk": 259,
            "fields": {
                "replaces": None,
                "enabled": True,
                "lastmodified": "2013-11-15T01:18:32Z",
                "uuid": "c6a208a1-8abc-47b9-9b1e-47c877aa4a0f",
                "format": "187d9216-7a53-4ef6-b9dd-4a397c414543",
                "version": "",
                "pronom_id": "",
                "description": "Archivematica Maildir",
                "access_format": False,
                "preservation_format": True,
                "slug": "archivematica-maildir",
            },
        },
    ]
    new_entries = new_formats + new_format_groups + new_format_versions
    new_json = old_json + new_entries

    old_json_path = tmp_path / "old.json"
    new_json_path = tmp_path / "new.json"
    output_path = tmp_path / "output"
    old_json_path.write_text(json.dumps(old_json))
    new_json_path.write_text(json.dumps(new_json))

    call_command(
        "get_fpr_changes", str(old_json_path), str(new_json_path), str(output_path)
    )

    captured = capsys.readouterr()
    assert (
        "\n".join(
            [
                f"{len(new_entries)} new entries total",
                f"{len(new_formats)} new entries for fpr.format",
                f"{len(new_format_groups)} new entries for fpr.formatgroup",
                f"{len(new_format_versions)} new entries for fpr.formatversion",
            ]
        )
        in captured.out
    )
    assert json.loads(output_path.read_text()) == [
        {"model": entry["model"], "fields": entry["fields"]} for entry in new_entries
    ]


def test_command_ignores_pk_and_lastmodified_differences(
    tmp_path: pathlib.Path,
) -> None:
    old_json = [
        {
            "model": "fpr.idcommand",
            "pk": 22,
            "fields": {
                "replaces": "88c747f5-7b6c-4913-8dc2-3957dcd5e6b8",
                "enabled": True,
                "lastmodified": "2026-07-13T23:50:32.442Z",
                "uuid": "4914841c-3555-4519-86e3-5bf622d28351",
                "tool": "454df69d-5cc0-49fc-93e4-6fbb6ac659e7",
                "description": "Identify using Siegfried 1.11.2",
                "config": "PUID",
                "script": "identify with siegfried",
                "script_type": "pythonScript",
            },
        }
    ]
    new_json = [
        {
            "model": "fpr.idcommand",
            "pk": 42,
            "fields": {
                "replaces": "88c747f5-7b6c-4913-8dc2-3957dcd5e6b8",
                "enabled": True,
                "lastmodified": "2026-07-14T15:03:17.078Z",
                "uuid": "4914841c-3555-4519-86e3-5bf622d28351",
                "tool": "454df69d-5cc0-49fc-93e4-6fbb6ac659e7",
                "description": "Identify using Siegfried 1.11.2",
                "config": "PUID",
                "script": "identify with siegfried",
                "script_type": "pythonScript",
            },
        }
    ]

    old_json_path = tmp_path / "old.json"
    new_json_path = tmp_path / "new.json"
    output_path = tmp_path / "output.json"
    old_json_path.write_text(json.dumps(old_json))
    new_json_path.write_text(json.dumps(new_json))

    call_command(
        "get_fpr_changes", str(old_json_path), str(new_json_path), str(output_path)
    )

    assert json.loads(output_path.read_text()) == []


def test_command_ignores_semantically_identical_entries_with_different_uuids(
    tmp_path: pathlib.Path,
) -> None:
    old_json = [
        {
            "model": "fpr.fprule",
            "pk": 872,
            "fields": {
                "replaces": None,
                "enabled": True,
                "lastmodified": "2026-07-13T23:50:32.719Z",
                "uuid": "8c128693-56c7-4798-90a8-bd939e86fb95",
                "purpose": "validation",
                "command": "09a14b6b-3f4c-49d8-9a62-0c7212aca83c",
                "format": "6ad6b8e1-0fc5-46ac-8531-28dbf5fe33c4",
                "count_attempts": 0,
                "count_okay": 0,
                "count_not_okay": 0,
            },
        }
    ]
    new_json = [
        {
            "model": "fpr.fprule",
            "pk": 872,
            "fields": {
                "replaces": None,
                "enabled": True,
                "lastmodified": "2026-07-14T15:03:17.188Z",
                "uuid": "6b8af700-b1a1-449a-81b0-2112307a3dae",
                "purpose": "validation",
                "command": "09a14b6b-3f4c-49d8-9a62-0c7212aca83c",
                "format": "6ad6b8e1-0fc5-46ac-8531-28dbf5fe33c4",
                "count_attempts": 0,
                "count_okay": 0,
                "count_not_okay": 0,
            },
        }
    ]

    old_json_path = tmp_path / "old.json"
    new_json_path = tmp_path / "new.json"
    output_path = tmp_path / "output.json"
    old_json_path.write_text(json.dumps(old_json))
    new_json_path.write_text(json.dumps(new_json))

    call_command(
        "get_fpr_changes", str(old_json_path), str(new_json_path), str(output_path)
    )

    assert json.loads(output_path.read_text()) == []


def test_command_rejects_new_entries_referencing_a_drifted_uuid(
    tmp_path: pathlib.Path,
) -> None:
    old_group_uuid = "49918a30-5db7-40f0-ac11-b56610365257"
    new_group_uuid = "27cb2790-d577-4411-9bcc-d78a27da1d01"
    old_json = [
        {
            "model": "fpr.formatgroup",
            "pk": 35,
            "fields": {
                "uuid": old_group_uuid,
                "description": "Text (Unstructured)",
                "slug": "text-unstructured",
            },
        }
    ]
    new_json = [
        {
            "model": "fpr.formatgroup",
            "pk": 35,
            "fields": {
                "uuid": new_group_uuid,
                "description": "Text (Unstructured)",
                "slug": "text-unstructured",
            },
        },
        {
            "model": "fpr.format",
            "pk": 1640,
            "fields": {
                "uuid": "86e2094e-8e1c-4c73-8c39-c341cb01a602",
                "description": "New text format",
                "group": new_group_uuid,
                "slug": "new-text-format",
            },
        },
    ]

    old_json_path = tmp_path / "old.json"
    new_json_path = tmp_path / "new.json"
    output_path = tmp_path / "output.json"
    old_json_path.write_text(json.dumps(old_json))
    new_json_path.write_text(json.dumps(new_json))

    with pytest.raises(CommandError) as exc_info:
        call_command(
            "get_fpr_changes",
            str(old_json_path),
            str(new_json_path),
            str(output_path),
        )

    assert str(exc_info.value) == (
        "New FPR entries reference UUIDs that identify semantically "
        f"unchanged records in the old FPR: {new_group_uuid}"
    )
    assert not output_path.exists()


def test_command_omits_primary_keys_from_output(tmp_path: pathlib.Path) -> None:
    new_entry = {
        "model": "fpr.formatgroup",
        "pk": 36,
        "fields": {
            "uuid": "35f8e190-b66e-4b90-92f1-15844d2211ea",
            "description": "New format group",
            "slug": "new-format-group",
        },
    }
    old_json_path = tmp_path / "old.json"
    new_json_path = tmp_path / "new.json"
    output_path = tmp_path / "output.json"
    old_json_path.write_text("[]")
    new_json_path.write_text(json.dumps([new_entry]))

    call_command(
        "get_fpr_changes", str(old_json_path), str(new_json_path), str(output_path)
    )

    assert json.loads(output_path.read_text()) == [
        {
            "model": new_entry["model"],
            "fields": new_entry["fields"],
        }
    ]
