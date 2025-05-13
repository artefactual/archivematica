import pathlib
import uuid
from unittest import mock

import pytest
import pytest_django
from django.core.management import call_command

from archivematica.dashboard.fpr.models import FormatGroup
from archivematica.dashboard.fpr.models import IDCommand


@pytest.fixture()
def unknown_format_group() -> FormatGroup:
    result, _ = FormatGroup.objects.get_or_create(
        uuid="00abbdd0-51b3-4162-b93a-45deb4ed8654", description="Unknown"
    )
    return result


@pytest.fixture()
def file_by_extension_command() -> IDCommand:
    result, _ = IDCommand.objects.get_or_create(
        uuid="8546b624-7894-4201-8df6-f239d5e0d5ba"
    )
    return result


@pytest.mark.django_db
def test_command_fails_if_xml_file_does_not_exist(
    tmp_path: pathlib.Path,
    unknown_format_group: FormatGroup,
    file_by_extension_command: IDCommand,
) -> None:
    with pytest.raises(SystemExit, match="Pronom XML file does not exist!"):
        call_command("import_pronom_ids", str(tmp_path / "bogus.xml"))


@pytest.mark.django_db
def test_command_saves_data_migration_to_file(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    settings: pytest_django.fixtures.SettingsWrapper,
    unknown_format_group: FormatGroup,
    file_by_extension_command: IDCommand,
) -> None:
    # Enable connection.queries used in the command.
    settings.DEBUG = True

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
            f"Format '{xml_format_name}' does not contain any PRONOM classifications. Setting the 'Unknown' group.",
        ]
    )
    assert output_file_path.read_text().strip() == "\n".join(
        [
            "def data_migration(apps, schema_editor):",
            "    Format = apps.get_model('fpr', 'Format')",
            "    FormatVersion = apps.get_model('fpr', 'FormatVersion')",
            "    IDRule = apps.get_model('fpr', 'IDRule')",
            "",
            f'    Format.objects.create(description="""{xml_format_name}""", group_id="{unknown_format_group.uuid}", uuid="{format_uuid}")',
            f'    FormatVersion.objects.create(format_id="{format_uuid}", pronom_id="{xml_format_puid}", description="""{xml_format_signature_name}""", version="{xml_format_version}", uuid="{format_version_uuid}")',
            f'    IDRule.objects.create(format_id="{format_version_uuid}", command_id="{file_by_extension_command.uuid}", command_output=".{xml_format_extension}")',
        ]
    )


@pytest.mark.django_db
def test_command_sets_format_group_from_pronom_classifications(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    settings: pytest_django.fixtures.SettingsWrapper,
    unknown_format_group: FormatGroup,
    file_by_extension_command: IDCommand,
) -> None:
    # Enable connection.queries used in the command.
    settings.DEBUG = True

    format_uuid = uuid.uuid4()
    format_version_uuid = uuid.uuid4()
    idrule_uuid = uuid.uuid4()

    format_group_description = "My format group"
    format_group = FormatGroup.objects.create(description=format_group_description)

    xml_format_puid = "fmt/8888888"
    xml_format_name = "My other format"
    xml_format_version = "1.0"
    xml_format_pronom_id = "1"
    xml_format_extension = "barbaz"
    xml_format_signature_name = "My other signature name"
    xml_format_pronom_classifications = format_group.description

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
                <details>
                    <content_type>{xml_format_pronom_classifications}</content_type>
                </details>
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
            f'    Format.objects.create(description="""{xml_format_name}""", group_id="{format_group.uuid}", uuid="{format_uuid}")',
            f'    FormatVersion.objects.create(format_id="{format_uuid}", pronom_id="{xml_format_puid}", description="""{xml_format_signature_name}""", version="{xml_format_version}", uuid="{format_version_uuid}")',
            f'    IDRule.objects.create(format_id="{format_version_uuid}", command_id="{file_by_extension_command.uuid}", command_output=".{xml_format_extension}")',
        ]
    )


@pytest.mark.django_db
def test_command_sets_unknown_format_group_if_multiple_pronom_classifications_exist(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    settings: pytest_django.fixtures.SettingsWrapper,
    unknown_format_group: FormatGroup,
    file_by_extension_command: IDCommand,
) -> None:
    # Enable connection.queries used in the command.
    settings.DEBUG = True

    format_uuid = uuid.uuid4()
    format_version_uuid = uuid.uuid4()
    idrule_uuid = uuid.uuid4()

    format_group_description = "My format group"
    format_group = FormatGroup.objects.create(description=format_group_description)

    another_format_group_description = "Another format group"
    another_format_group = FormatGroup.objects.create(
        description=another_format_group_description
    )

    xml_format_puid = "fmt/7777777"
    xml_format_name = another_format_group_description
    xml_format_version = "1.0"
    xml_format_pronom_id = "1"
    xml_format_extension = "some"
    xml_format_signature_name = "Some other signature name"
    xml_format_pronom_classifications = ", ".join(
        [format_group.description, another_format_group.description]
    )

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
                <details>
                    <content_type>{xml_format_pronom_classifications}</content_type>
                </details>
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
            f"Format '{another_format_group_description}' contains multiple PRONOM classifications '{xml_format_pronom_classifications}'. Setting the 'Unknown' group.",
        ]
    )
    assert output_file_path.read_text().strip() == "\n".join(
        [
            "def data_migration(apps, schema_editor):",
            "    Format = apps.get_model('fpr', 'Format')",
            "    FormatVersion = apps.get_model('fpr', 'FormatVersion')",
            "    IDRule = apps.get_model('fpr', 'IDRule')",
            "",
            f'    Format.objects.create(description="""{xml_format_name}""", group_id="{unknown_format_group.uuid}", uuid="{format_uuid}")',
            f'    FormatVersion.objects.create(format_id="{format_uuid}", pronom_id="{xml_format_puid}", description="""{xml_format_signature_name}""", version="{xml_format_version}", uuid="{format_version_uuid}")',
            f'    IDRule.objects.create(format_id="{format_version_uuid}", command_id="{file_by_extension_command.uuid}", command_output=".{xml_format_extension}")',
        ]
    )


@pytest.mark.django_db
def test_command_sets_unknown_format_group_if_pronom_classifications_do_not_exist(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    settings: pytest_django.fixtures.SettingsWrapper,
    unknown_format_group: FormatGroup,
    file_by_extension_command: IDCommand,
) -> None:
    # Enable connection.queries used in the command.
    settings.DEBUG = True

    format_uuid = uuid.uuid4()
    format_version_uuid = uuid.uuid4()
    idrule_uuid = uuid.uuid4()

    xml_format_puid = "fmt/666666"
    xml_format_name = "My bogus format"
    xml_format_version = "1.0"
    xml_format_pronom_id = "1"
    xml_format_extension = "bogus"
    xml_format_signature_name = "Some bogus signature name"
    xml_format_pronom_classifications = "Bogus"

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
                <details>
                    <content_type>{xml_format_pronom_classifications}</content_type>
                </details>
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
            f"Could not match an existing format group for format '{xml_format_name}' from its PRONOM classification '{xml_format_pronom_classifications}'. Setting the 'Unknown' group instead.",
        ]
    )
    assert output_file_path.read_text().strip() == "\n".join(
        [
            "def data_migration(apps, schema_editor):",
            "    Format = apps.get_model('fpr', 'Format')",
            "    FormatVersion = apps.get_model('fpr', 'FormatVersion')",
            "    IDRule = apps.get_model('fpr', 'IDRule')",
            "",
            f'    Format.objects.create(description="""{xml_format_name}""", group_id="{unknown_format_group.uuid}", uuid="{format_uuid}")',
            f'    FormatVersion.objects.create(format_id="{format_uuid}", pronom_id="{xml_format_puid}", description="""{xml_format_signature_name}""", version="{xml_format_version}", uuid="{format_version_uuid}")',
            f'    IDRule.objects.create(format_id="{format_version_uuid}", command_id="{file_by_extension_command.uuid}", command_output=".{xml_format_extension}")',
        ]
    )
