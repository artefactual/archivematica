# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import sys
import uuid

from django.core.management.base import BaseCommand
from django.db import connection

from fpr.models import Format, FormatGroup, FormatVersion, IDCommand, IDRule

from lxml import etree


archivematica_formats = {}
unknown_format_group = FormatGroup.objects.get(description="Unknown")
file_by_extension = IDCommand.objects.get(description="Identify by File Extension")

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


class PronomFormat(object):
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
        try:
            FormatVersion.objects.get(pronom_id=puid)
            print("Ignoring {}".format(puid))
            continue
        except (FormatVersion.DoesNotExist, FormatVersion.MultipleObjectsReturned):
            print("DOES NOT EXIST OK!")
            pass

        new_format = PronomFormat(format)
        print("Importing", new_format.version_name, file=sys.stderr)
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
                migration = """    Format.objects.create(description="{}", group_id="{}", uuid="{}")""".format(
                    new_format.format_name,
                    unknown_format_group.uuid,
                    parent_format.uuid,
                )
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
        migration = """    FormatVersion.objects.create(format_id="{}", pronom_id="{}", description="{}", version="{}", uuid="{}")""".format(
            parent_format.uuid,
            new_format.puid,
            new_format.version_name,
            new_format.version,
            format_version.uuid,
        )
        choose_output(output_format, output_file, sql, migration)

        # If an extension is listed, set up a new IDRule so that
        # the `Files by Extension` IDCommand can find them.
        if new_format.extension:
            # First check to see if a rule already exists: if it does, delete it
            # IDRules can only map an extension to a single format and we don't know which extension to map to.
            try:
                rule = IDRule.objects.get(command_output=new_format.extension)
                rule.delete()
                sql = connection.queries[-1]["sql"]
                migration = """    IDRule.objects.filter(command_output="{}").delete()""".format(
                    new_format.extension
                )
                choose_output(output_format, output_file, sql, migration)
            except IDRule.DoesNotExist:
                rule = IDRule(
                    format=format_version,
                    command=file_by_extension,
                    command_output=new_format.extension,
                )
                sql = save_object(rule)
                migration = """    IDRule.objects.create(format_id="{}", command_id="{}", command_output="{}")""".format(
                    format_version.uuid, file_by_extension.uuid, new_format.extension
                )
                choose_output(output_format, output_file, sql, migration)
        print(file=output_file)
