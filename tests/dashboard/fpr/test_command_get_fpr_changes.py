import json
import pathlib

import pytest
from django.core.management import call_command


@pytest.mark.django_db
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
    assert json.loads(output_path.read_text()) == new_entries
