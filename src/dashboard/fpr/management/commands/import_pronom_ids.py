import os
import sys
import uuid
from typing import Dict

from django.core.management.base import BaseCommand
from django.db import connection
from fpr.models import Format
from fpr.models import FormatGroup
from fpr.models import FormatVersion
from fpr.models import IDCommand
from fpr.models import IDRule
from lxml import etree

# Introduced in fpr/migrations/0035_python3_compatibility.py
FILE_BY_EXTENSION_CMD_UUID = "8546b624-7894-4201-8df6-f239d5e0d5ba"

archivematica_formats: Dict[str, Format] = {}
unknown_format_group = FormatGroup.objects.get(description="Unknown")
file_by_extension = IDCommand.objects.get(uuid=FILE_BY_EXTENSION_CMD_UUID)

SQL_OUTPUT = "sql"
MIGRATIONS_OUTPUT = "migration"


class Command(BaseCommand):
    help = "Import formats from PRONOM"

    def add_arguments(self, parser):
        parser.add_argument("pronom_xml", help="Path to FIDO PRONOM XML file")
        parser.add_argument(
            "--output-format",
            choices=[SQL_OUTPUT, MIGRATIONS_OUTPUT],
            help="What format to output the updates as",
            default=MIGRATIONS_OUTPUT,
        )
        parser.add_argument(
            "--output-filename",
            "-o",
            help='File to output the migration to. "stdout" outputs to '
            "standard output",
            default="stdout",
        )

    def handle(self, *args, **options):
        if not os.path.exists(options["pronom_xml"]):
            sys.exit("Pronom XML file does not exist!")

        output_file = sys.stdout
        if options["output_filename"] != "stdout":
            output_file = open(options["output_filename"], "w")

        try:
            rc = main(options["pronom_xml"], options["output_format"], output_file)
        finally:
            if output_file != sys.stdout:
                output_file.close()

        sys.exit(rc)


def save_object(obj):
    obj.save()
    return connection.queries[-1]["sql"]


def choose_output(output_format, output_file, sql, migration):
    if output_format == SQL_OUTPUT:
        print(sql, ";", file=output_file)
    elif output_format == MIGRATIONS_OUTPUT:
        print(migration, file=output_file)


class PronomFormat:
    def __init__(self, xml):
        self.puid = xml.find(".puid").text
        self.format_name = xml.find(".name").text
        signature = xml.find(".signature")
        if signature is not None:
            self.version_name = xml.find(".signature/name").text
        # Unfortunately, certain formats don't have signatures, and
        # thus are missing the more specific name.
        # In that scenario we just have to use the same string for both.
        else:
            self.version_name = self.format_name

        # This field only allows 10 characters in the FPR database;
        # just don't save this if it's too long.
        self.version = xml.find(".version").text
        if self.version and len(self.version) > 10:
            self.version = ""

        extension = xml.find(".extension")
        if extension is not None and extension.text:
            self.extension = "." + extension.text
        else:
            self.extension = None


def main(pronom_xml, output_format=SQL_OUTPUT, output_file=sys.stdout):
    formats = etree.parse(pronom_xml)
    if output_format == MIGRATIONS_OUTPUT:
        print("def data_migration(apps, schema_editor):", file=output_file)
        print("    Format = apps.get_model('fpr', 'Format')", file=output_file)
        print(
            "    FormatVersion = apps.get_model('fpr', 'FormatVersion')",
            file=output_file,
        )
        print("    IDRule = apps.get_model('fpr', 'IDRule')", file=output_file)
        print(file=output_file)

    for format in formats.getroot():
        puid = format.find(".puid").text
        # fmt/111 is "OLE2 Compound Document Format".
        # Many Windows file formats that aren't otherwise IDed will
        # be identified as this. We choose not to import this one
        # ID in order to allow Archivematica to recognize those files
        # as unidentified instead of returning something misleading.
        if puid == "fmt/111":
            continue
        # If a FormatVersion with this PUID already exists,
        # we don't want to do anything.
        if FormatVersion.objects.filter(pronom_id=puid).exists():
            print(f"Ignoring {puid}")
            continue

        print(f"Format {puid} does not exist")
        new_format = PronomFormat(format)
        print("Importing", new_format.version_name, new_format.puid)
        parent_format = archivematica_formats.get(new_format.format_name)
        if not parent_format:
            try:
                parent_format = Format.objects.get(description=new_format.format_name)
            except Format.DoesNotExist:
                parent_format = Format(
                    description=new_format.format_name,
                    group=unknown_format_group,
                    uuid=str(uuid.uuid4()),
                )
                migration = f'''    Format.objects.create(description="""{new_format.format_name}""", group_id="{unknown_format_group.uuid}", uuid="{parent_format.uuid}")'''
                sql = save_object(parent_format)
                choose_output(output_format, output_file, sql, migration)
                archivematica_formats[new_format.format_name] = parent_format

        format_version = FormatVersion(
            format=parent_format,
            pronom_id=new_format.puid,
            description=new_format.version_name,
            version=new_format.version,
            uuid=str(uuid.uuid4()),
        )
        sql = save_object(format_version)
        migration = f'''    FormatVersion.objects.create(format_id="{parent_format.uuid}", pronom_id="{new_format.puid}", description="""{new_format.version_name}""", version="{new_format.version}", uuid="{format_version.uuid}")'''
        choose_output(output_format, output_file, sql, migration)

        # If an extension is listed, set up a new IDRule so that
        # the `Files by Extension` IDCommand can find them.
        if new_format.extension:
            # First check to see if rules already exist: if they do, delete them
            # IDRules can only map an extension to a single format and we don't know which extension to map to.
            deleted_count, _ = rule = IDRule.objects.filter(
                command_output=new_format.extension
            ).delete()
            if deleted_count:
                sql = connection.queries[-1]["sql"]
                migration = f"""    IDRule.objects.filter(command_output="{new_format.extension}").delete()"""
                choose_output(output_format, output_file, sql, migration)
            else:
                rule = IDRule(
                    format=format_version,
                    command=file_by_extension,
                    command_output=new_format.extension,
                )
                sql = save_object(rule)
                migration = f"""    IDRule.objects.create(format_id="{format_version.uuid}", command_id="{file_by_extension.uuid}", command_output="{new_format.extension}")"""
                choose_output(output_format, output_file, sql, migration)
        print(file=output_file)
