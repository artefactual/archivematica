import pathlib
import uuid
from unittest import mock

import pytest
import pytest_django
from django.core.management import call_command


@pytest.mark.django_db
def test_command_fails_if_xml_file_does_not_exist(tmp_path: pathlib.Path) -> None:
    with pytest.raises(SystemExit, match="Pronom XML file does not exist!"):
        call_command("import_pronom_ids", str(tmp_path / "bogus.xml"))


@pytest.mark.django_db
def test_command_saves_data_migration_to_file(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    # Enable connection.queries used in the command.
    settings.DEBUG = True

    # These identifiers are hardcoded in the command.
    file_by_extension_command_uuid = uuid.UUID("8546b624-7894-4201-8df6-f239d5e0d5ba")
    unknown_group_uuid = uuid.UUID("00abbdd0-51b3-4162-b93a-45deb4ed8654")

    format_uuid = uuid.uuid4()
    format_version_uuid = uuid.uuid4()
    idrule_uuid = uuid.uuid4()

    xml_format_puid = "fmt/9999999"
    xml_format_name = "My new format"
    xml_format_version = "1.0"
    xml_format_pronom_id = "1"
    xml_format_extension = "foobar"
    xml_format_signature_name = "My signature name"

    output_file_path = tmp_path / "output.xml"
    pronom_xml_path = tmp_path / "pronom.xml"
    pronom_xml_path.write_text(f"""
        <formats>
            <format>
                <puid>{xml_format_puid}</puid>
                <name>{xml_format_name}</name>
                <version>{xml_format_version}</version>
                <pronom_id>{xml_format_pronom_id}</pronom_id>
                <extension>{xml_format_extension}</extension>
                <signature>
                    <name>{xml_format_signature_name}</name>
                </signature>
            </format>
        </formats>
    """)

    with mock.patch(
        "uuid.uuid4", side_effect=[format_uuid, format_version_uuid, idrule_uuid]
    ):
        with pytest.raises(SystemExit) as excinfo:
            call_command(
                "import_pronom_ids",
                "--output-filename",
                str(output_file_path),
                "--output-format",
                "migration",
                str(pronom_xml_path),
            )
        assert excinfo.value.code is None

    captured = capsys.readouterr()
    assert captured.out.strip() == "\n".join(
        [
            f"Format {xml_format_puid} does not exist",
            f"Importing {xml_format_signature_name} {xml_format_puid}",
        ]
    )
    assert output_file_path.read_text().strip() == "\n".join(
        [
            "def data_migration(apps, schema_editor):",
            "    Format = apps.get_model('fpr', 'Format')",
            "    FormatVersion = apps.get_model('fpr', 'FormatVersion')",
            "    IDRule = apps.get_model('fpr', 'IDRule')",
            "",
            f'    Format.objects.create(description="""{xml_format_name}""", group_id="{unknown_group_uuid}", uuid="{format_uuid}")',
            f'    FormatVersion.objects.create(format_id="{format_uuid}", pronom_id="{xml_format_puid}", description="""{xml_format_signature_name}""", version="{xml_format_version}", uuid="{format_version_uuid}")',
            f'    IDRule.objects.create(format_id="{format_version_uuid}", command_id="{file_by_extension_command_uuid}", command_output=".{xml_format_extension}")',
        ]
    )
