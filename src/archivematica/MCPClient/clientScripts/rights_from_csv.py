#!/usr/bin/env python
# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import annotations

import csv
import os
from collections.abc import Iterable

import django

django.setup()
from django.db import models as django_models
from django.db import transaction

from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job

RightsRow = dict[str, str | None]
RightsRows = list[tuple[int, RightsRow]]


class RightsRowException(Exception):
    def __init__(self, message: str, reader: RightCsvReader) -> None:
        message = f"[Row {reader.rows_processed + 1}] {message}"
        super().__init__(message)


class MissingTransferFilesException(Exception):
    """Raised when rights.csv references files missing from the transfer."""


class RightCsvReader:
    metadata_applies_to_type: models.MetadataAppliesToType | None = None
    current_row: RightsRow | None = None
    rows_processed = 0

    required_column_names = ["file"]

    optional_column_names = [
        "basis",
        "status",  # mandatory for copyright
        "determination_date",
        "start_date",
        "end_date",
        "jurisdiction",  # mandatory for copyright and statute basis
        "terms",
        "citation",  # mandatory for statute basis
        "note",
        "grant_act",
        "grant_restriction",
        "grant_start_date",
        "grant_end_date",
        "grant_note",
        "doc_id_type",
        "doc_id_value",
        "doc_id_role",
    ]

    allowed_column_names = optional_column_names + required_column_names

    def __init__(self, job: Job, transfer_uuid: str, rights_csv_filepath: str) -> None:
        """Initialize parser."""
        # self.allowed_column_names = self.optional_column_names + self.required_column_names
        self.transfer_uuid = transfer_uuid
        self.rights_csv_filepath = rights_csv_filepath
        self.job = job
        self.object_basis_act_usage: dict[str, dict[str, dict[str | None, bool]]] = {}
        self.current_row = None
        self.rows_processed = 0
        self.has_act = False
        self.transfer_files_by_path: dict[bytes, models.File] = {}

    def parse(self) -> int:
        """Read and parse rights CSV file."""
        # Cache metadata applies to type
        self.metadata_applies_to_type = models.MetadataAppliesToType.objects.filter(
            description="File"
        ).first()

        # Use universal newline mode to support unusual newlines, like \r
        with open(self.rights_csv_filepath) as f:
            reader = csv.DictReader(f)
            rows: RightsRows = list(enumerate(reader, start=2))

        if rows:
            self.validate_columns(rows[0][1])
            self.validate_transfer_files(rows)

        for _, row in rows:
            self.parse_row(row)

        return self.rows_processed

    def validate_transfer_files(self, rows: RightsRows) -> None:
        """Check that all files listed in rights.csv exist in the transfer."""
        path_rows: list[tuple[int, bytes]] = []
        missing_paths: list[str] = []

        for row_number, row in rows:
            raw_filepath = row.get("file")
            if raw_filepath is None:
                continue

            filepath = raw_filepath.strip()
            if not filepath:
                continue

            path = self.transfer_path(filepath)
            path_rows.append((row_number, path))

        paths = {path for _, path in path_rows}
        self.transfer_files_by_path = {
            bytes(file_.originallocation): file_
            for file_ in models.File.objects.filter(
                originallocation__in=paths,
                transfer_id=self.transfer_uuid,
            )
        }

        for row_number, path in path_rows:
            if path not in self.transfer_files_by_path:
                missing_paths.append(f"[Row {row_number}] {path.decode()}")

        if not missing_paths:
            return

        raise MissingTransferFilesException(
            "Files listed in rights.csv were not found in the transfer "
            f"(transfer UUID: {self.transfer_uuid}):\n" + "\n".join(missing_paths)
        )

    def transfer_path(self, filepath: str) -> bytes:
        return f"%transferDirectory%{filepath}".encode()

    def required_column_value(self, column_name: str) -> str:
        value = self.column_value(column_name)
        if value is None:
            raise RightsRowException(f"Missing required value: {column_name}", self)
        return value

    def parse_row(self, row: RightsRow) -> None:
        """Parse a row of a CSV file and create rights records in database."""
        if self.current_row is None:
            self.validate_columns(row)

        self.current_row = row

        # If no file specified, fail
        filepath = self.column_value("file")
        if not filepath:
            raise RightsRowException("No file specified", self)

        # If restriction specified, ensure it has an allowed value
        restriction = self.column_value("grant_restriction")
        if restriction and restriction.lower() not in [
            "disallow",
            "conditional",
            "allow",
        ]:
            raise RightsRowException(
                "The value of element restriction must be: 'Allow', 'Disallow', or 'Conditional'",
                self,
            )

        # Initialize hash to note which basis/act combinations for file have alredy been imported
        if filepath not in self.object_basis_act_usage:
            self.object_basis_act_usage[filepath] = {}

        basis = self.required_column_value("basis").lower().capitalize()

        if basis not in self.object_basis_act_usage[filepath]:
            self.object_basis_act_usage[filepath][basis] = {}

        # Check that act is set and normalize value
        self.has_act = False
        act = self.column_value("grant_act")
        if act:
            act = act.lower().capitalize()
            self.has_act = True

        # Process row if basis/act combination for file hasn't yet been imported
        if act not in self.object_basis_act_usage[filepath][basis]:
            self.store_row()
            self.object_basis_act_usage[filepath][basis][act] = True
        else:
            self.job.pyprint(
                "Skipping duplicate basis/act combination at row",
                self.rows_processed + 1,
            )

        self.rows_processed += 1

    def store_row(self) -> None:
        """Create rights records in database using row data."""
        rights_statement = self.generate_rights_statement()

        if rights_statement.rightsbasis == "Copyright":
            self.store_copyright_info(rights_statement)

        elif rights_statement.rightsbasis == "License":
            self.store_license_info(rights_statement)

        elif rights_statement.rightsbasis == "Statute":
            self.store_statute_info(rights_statement)

        elif rights_statement.rightsbasis in ["Other", "Donor", "Policy"]:
            self.store_other_info(rights_statement)

        if self.has_act:
            self.store_grant_info(rights_statement)

    def generate_rights_statement(self) -> models.RightsStatement:
        """Generate rights statement."""
        basis = self.required_column_value("basis").lower().capitalize()

        if basis not in dict(models.RightsStatement.RIGHTS_BASIS_CHOICES):
            raise RightsRowException(f"Invalid basis: {basis}", self)

        # Get file data
        filepath = self.required_column_value("file")
        path = self.transfer_path(filepath)
        transfer_file = self.transfer_files_by_path.get(path)
        if transfer_file is None:
            transfer_file = models.File.objects.get(
                originallocation=path,
                transfer_id=self.transfer_uuid,
            )

        # Create rights statement
        rights_statement = models.RightsStatement()
        if self.metadata_applies_to_type is None:
            raise RuntimeError("Unable to find File metadata applies to type")

        rights_statement.metadataappliestotype = self.metadata_applies_to_type
        rights_statement.metadataappliestoidentifier = str(transfer_file.uuid)
        rights_statement.rightsbasis = basis
        rights_statement.status = "ORIGINAL"
        rights_statement.save()

        return rights_statement

    def validate_columns(self, row: RightsRow) -> None:
        """Check for invalid/missing columns."""
        for column_name in row.keys():
            if column_name not in self.allowed_column_names:
                raise RightsRowException(f"Invalid column found: {column_name}", self)

        for column_name in self.required_column_names:
            if column_name not in row:
                raise RightsRowException(
                    f"Missing required column: {column_name}", self
                )

    def column_value(self, column_name: str) -> str | None:
        """Return value of a row column by it's name in the header, None if missing/blank."""
        if self.current_row is None:
            return None

        value = self.current_row.get(column_name)
        if value is None:
            return None

        value = value.strip()
        return value if value else None

    def set_model_instance_attribute_to_row_column_if_set(
        self, model_instance: django_models.Model, attribute: str, column_name: str
    ) -> None:
        """Check if a column has a value and, if so, set a model instance's attribute to that value."""
        value = self.column_value(column_name)
        if value is not None:
            setattr(model_instance, attribute, value)

    def set_model_instance_attributes_to_row_columns_if_set(
        self,
        model_instance: django_models.Model,
        attribute_to_column_map: dict[str, str],
    ) -> None:
        """Using a dict that maps model attributes to column names, set a model instance's attributes."""
        for attribute, column_name in attribute_to_column_map.items():
            self.set_model_instance_attribute_to_row_column_if_set(
                model_instance, attribute, column_name
            )

    def store_doc_id(
        self,
        model: type[django_models.Model],
        parent_instance: django_models.Model,
        parent_property: str,
        type_property: str,
        value_property: str,
        role_property: str,
    ) -> None:
        """Optionally store documentation identifier info."""
        id_type = self.column_value("doc_id_type")
        id_value = self.column_value("doc_id_value")
        id_role = self.column_value("doc_id_role")

        if id_type or id_value or id_role:
            doc_id = model()
            setattr(doc_id, parent_property, parent_instance)
            copyright_parent_property = "rightscopyright"
            setattr(doc_id, copyright_parent_property, parent_instance)
            self.set_model_instance_attribute_to_row_column_if_set(
                doc_id, type_property, "doc_id_type"
            )
            self.set_model_instance_attribute_to_row_column_if_set(
                doc_id, value_property, "doc_id_value"
            )
            self.set_model_instance_attribute_to_row_column_if_set(
                doc_id, role_property, "doc_id_role"
            )
            doc_id.save()

    def store_copyright_info(self, rights_statement: models.RightsStatement) -> None:
        """Store copyright-specific column values in the database."""
        copyright_info = models.RightsStatementCopyright()
        copyright_info.rightsstatement = rights_statement

        attribute_to_column_map = {
            "copyrightstatus": "status",
            "copyrightjurisdiction": "jurisdiction",
            "copyrightstatusdeterminationdate": "determination_date",
            "copyrightapplicablestartdate": "start_date",
        }

        self.set_model_instance_attributes_to_row_columns_if_set(
            copyright_info, attribute_to_column_map
        )

        end_date = self.column_value("end_date")
        if end_date and end_date.lower() == "open":
            copyright_info.copyrightenddateopen = True
        elif end_date:
            copyright_info.copyrightapplicableenddate = end_date

        copyright_info.save()

        # Optionally store documentation identifier
        self.store_doc_id(
            models.RightsStatementCopyrightDocumentationIdentifier,
            copyright_info,
            "rightscopyright",
            "copyrightdocumentationidentifiertype",
            "copyrightdocumentationidentifiervalue",
            "copyrightdocumentationidentifierrole",
        )

        # Optionally store note
        note_value = self.column_value("note")
        if note_value:
            note = models.RightsStatementCopyrightNote()
            note.rightscopyright = copyright_info
            note.copyrightnote = note_value
            note.save()

    def store_license_info(self, rights_statement: models.RightsStatement) -> None:
        """Store licensing-specific column values in the database."""
        license_info = models.RightsStatementLicense()
        license_info.rightsstatement = rights_statement
        self.set_model_instance_attributes_to_row_columns_if_set(
            license_info,
            {
                "licenseterms": "terms",
                "licenseapplicablestartdate": "start_date",
            },
        )

        end_date = self.column_value("end_date")
        if end_date and end_date.lower() == "open":
            license_info.licenseenddateopen = True
        elif end_date:
            license_info.licenseapplicableenddate = end_date

        license_info.save()

        # Optionally store documentation identifier
        self.store_doc_id(
            models.RightsStatementLicenseDocumentationIdentifier,
            license_info,
            "rightsstatementlicense",
            "licensedocumentationidentifiertype",
            "licensedocumentationidentifiervalue",
            "licensedocumentationidentifierrole",
        )

        # Optionally store note
        note_value = self.column_value("note")
        if note_value:
            note = models.RightsStatementLicenseNote()
            note.rightsstatementlicense = license_info
            note.licensenote = note_value
            note.save()

    def store_statute_info(self, rights_statement: models.RightsStatement) -> None:
        """Store statute-specific column values in the database."""
        statute_info = models.RightsStatementStatuteInformation()
        statute_info.rightsstatement = rights_statement
        self.set_model_instance_attributes_to_row_columns_if_set(
            statute_info,
            {
                "statutejurisdiction": "jurisdiction",
                "statutecitation": "citation",
                "statutedeterminationdate": "determination_date",
                "statuteapplicablestartdate": "start_date",
            },
        )

        end_date = self.column_value("end_date")
        if end_date and end_date.lower() == "open":
            statute_info.statuteenddateopen = True
        elif end_date:
            statute_info.statuteapplicableenddate = end_date

        statute_info.save()

        # Optionally store documentation identifier
        self.store_doc_id(
            models.RightsStatementStatuteDocumentationIdentifier,
            statute_info,
            "rightsstatementstatute",
            "statutedocumentationidentifiertype",
            "statutedocumentationidentifiervalue",
            "statutedocumentationidentifierrole",
        )

        # Optionally store note
        note_value = self.column_value("note")
        if note_value:
            note = models.RightsStatementStatuteInformationNote()
            note.rightsstatementstatute = statute_info
            note.statutenote = note_value
            note.save()

    def store_other_info(self, rights_statement: models.RightsStatement) -> None:
        """Store "other" basis column values in the database."""
        other_info = models.RightsStatementOtherRightsInformation()
        other_info.rightsstatement = rights_statement
        other_info.otherrightsbasis = (
            self.required_column_value("basis").lower().capitalize()
        )
        self.set_model_instance_attribute_to_row_column_if_set(
            other_info, "otherrightsapplicablestartdate", "start_date"
        )

        end_date = self.column_value("end_date")
        if end_date and end_date.lower() == "open":
            other_info.otherrightsenddateopen = True
        elif end_date:
            other_info.otherrightsapplicableenddate = end_date

        other_info.save()

        # Optionally store documentation identifier
        self.store_doc_id(
            models.RightsStatementOtherRightsDocumentationIdentifier,
            other_info,
            "rightsstatementotherrights",
            "otherrightsdocumentationidentifiertype",
            "otherrightsdocumentationidentifiervalue",
            "otherrightsdocumentationidentifierrole",
        )

        # Optionally store note
        note_value = self.column_value("note")
        if note_value:
            note = models.RightsStatementOtherRightsInformationNote()
            note.rightsstatementotherrights = other_info
            note.otherrightsnote = note_value
            note.save()

    def store_grant_info(self, rights_statement: models.RightsStatement) -> None:
        """Store grant information in the database."""
        grant_info = models.RightsStatementRightsGranted()
        grant_info.rightsstatement = rights_statement
        grant_info.act = self.required_column_value("grant_act")
        self.set_model_instance_attribute_to_row_column_if_set(
            grant_info, "startdate", "grant_start_date"
        )

        end_date = self.column_value("grant_end_date")
        if end_date and end_date.lower() == "open":
            grant_info.enddateopen = True
        elif end_date:
            grant_info.enddate = end_date

        grant_info.save()

        # Optionally store restriction
        grant_restriction = self.column_value("grant_restriction")
        if grant_restriction:
            restriction = models.RightsStatementRightsGrantedRestriction()
            restriction.rightsgranted = grant_info
            restriction.restriction = grant_restriction
            restriction.save()

        # Optionally store note
        grant_note = self.column_value("grant_note")
        if grant_note:
            note = models.RightsStatementRightsGrantedNote()
            note.rightsgranted = grant_info
            note.rightsgrantednote = grant_note
            note.save()


def call(jobs: Iterable[Job]) -> None:
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                transfer_uuid = job.args[1]
                rights_csv_filepath = job.args[2]

                if os.path.isfile(rights_csv_filepath):
                    job.pyprint("Attempting to import rights data...")
                    try:
                        parser = RightCsvReader(job, transfer_uuid, rights_csv_filepath)
                        rows_processed = parser.parse()
                        job.pyprint("Processed rows:", rows_processed)
                    except (RightsRowException, MissingTransferFilesException) as err:
                        job.print_error(repr(err))
                        job.set_status(1)
                else:
                    job.pyprint("No rights.csv file found at", rights_csv_filepath)
