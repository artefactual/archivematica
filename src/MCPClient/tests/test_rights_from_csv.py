# -*- coding: utf8
from __future__ import print_function

import os
import sys

from django.test import TestCase

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

from main import models

from job import Job
import rights_from_csv


class TestRightsImportFromCsvBase(TestCase):

    transfer_uuid = "e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6"  # UUID of transfer created by transfer.json
    file_1_uuid = "47813453-6872-442b-9d65-6515be3c5aa1"  # UUID of first file created by files-transfer.json fixture
    file_2_uuid = "60e5c61b-14ef-4e92-89ec-9b9201e68adb"  # UUID of second file created by files-transfer.json fixture

    def get_metadata_applies_to_type_for_file(self):
        """ Get MetadataAppliesToType instance that allies to files. """
        return models.MetadataAppliesToType.objects.filter(description="File").first()


class TestRightsImportFromCsv(TestRightsImportFromCsvBase):
    """Test rights importing from CSV files."""

    fixture_files = [
        "metadata_applies_to_type.json",
        "transfer.json",
        "files-transfer.json",
    ]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def test_rows_processed_and_database_content(self):
        """Test CSV import using the RightsReader class.

        It should process valid rows of the CSV file.
        It should skip the third row data as basis/act is duplicate of earlier row.
        It should populate the rights-related models using data from the CSV file.
        """
        rights_csv_filepath = os.path.join(THIS_DIR, "fixtures/rights.csv")
        parser = rights_from_csv.RightCsvReader(
            Job("stub", "stub", []), self.transfer_uuid, rights_csv_filepath
        )
        rows_processed = parser.parse()

        # Test rows processed and model intance counts
        assert rows_processed == 8
        assert (
            models.RightsStatement.objects.count() == 7
        )  # One row in fixture CSV skipped due to duplicate basis/act combination
        assert models.RightsStatementLicense.objects.count() == 1
        assert models.RightsStatementCopyright.objects.count() == 2
        assert models.RightsStatementStatuteInformation.objects.count() == 1
        assert models.RightsStatementOtherRightsInformation.objects.count() == 3
        assert (
            models.RightsStatementCopyrightDocumentationIdentifier.objects.count() == 2
        )
        assert models.RightsStatementCopyrightNote.objects.count() == 2
        assert models.RightsStatementLicenseDocumentationIdentifier.objects.count() == 1
        assert models.RightsStatementLicenseNote.objects.count() == 1
        assert models.RightsStatementStatuteDocumentationIdentifier.objects.count() == 1
        assert models.RightsStatementStatuteInformationNote.objects.count() == 1
        assert (
            models.RightsStatementOtherRightsDocumentationIdentifier.objects.count()
            == 0
        )  # Not created as all related columns are blank
        assert models.RightsStatementOtherRightsInformationNote.objects.count() == 1
        assert models.RightsStatementRightsGranted.objects.count() == 7
        assert models.RightsStatementRightsGrantedRestriction.objects.count() == 5
        assert models.RightsStatementRightsGrantedNote.objects.count() == 3

        # Test row 1
        row_1_rights_statement = models.RightsStatement.objects.order_by("pk")[0]
        assert (
            row_1_rights_statement.metadataappliestotype
            == self.get_metadata_applies_to_type_for_file()
        )
        assert row_1_rights_statement.metadataappliestoidentifier == self.file_1_uuid
        assert row_1_rights_statement.status == "ORIGINAL"
        assert row_1_rights_statement.rightsbasis == "Copyright"

        row_1_copyright_info = models.RightsStatementCopyright.objects.order_by("pk")[0]
        assert row_1_copyright_info.rightsstatement == row_1_rights_statement
        assert row_1_copyright_info.copyrightstatus == "cop status"
        assert row_1_copyright_info.copyrightjurisdiction == "cop juris"
        assert row_1_copyright_info.copyrightstatusdeterminationdate == "2001-01-01"
        assert row_1_copyright_info.copyrightapplicablestartdate == "2002-02-02"
        assert row_1_copyright_info.copyrightenddateopen is False
        assert row_1_copyright_info.copyrightapplicableenddate == "2003-03-03"

        row_1_copyright_identifier = (
            models.RightsStatementCopyrightDocumentationIdentifier.objects.order_by(
                "pk"
            )[0]
        )
        assert (
            row_1_copyright_identifier.copyrightdocumentationidentifiertype
            == "cop type"
        )
        assert (
            row_1_copyright_identifier.copyrightdocumentationidentifierrole
            == "cop role"
        )

        row_1_copyright_note = models.RightsStatementCopyrightNote.objects.order_by(
            "pk"
        )[0]
        assert row_1_copyright_note.rightscopyright == row_1_copyright_info
        assert row_1_copyright_note.copyrightnote == "cop note"

        row_1_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[0]
        assert row_1_grant.rightsstatement == row_1_rights_statement
        assert row_1_grant.act == "cop act"
        assert row_1_grant.startdate == "2004-04-04"
        assert row_1_grant.enddateopen is False
        assert row_1_grant.enddate == "2005-05-05"

        row_1_restriction = (
            models.RightsStatementRightsGrantedRestriction.objects.order_by("pk")[0]
        )
        assert row_1_restriction.rightsgranted == row_1_grant
        assert row_1_restriction.restriction == "Allow"

        row_1_grant_note = models.RightsStatementRightsGrantedNote.objects.order_by(
            "pk"
        )[0]
        assert row_1_grant_note.rightsgranted == row_1_grant
        assert row_1_grant_note.rightsgrantednote == "cop grant note"

        # Test row 3 (row 2 is skipped as it has the same act and basis as a previous right for the file)
        row_3_rights_statement = models.RightsStatement.objects.order_by("pk")[1]
        assert (
            row_3_rights_statement.metadataappliestotype
            == self.get_metadata_applies_to_type_for_file()
        )
        assert row_3_rights_statement.metadataappliestoidentifier == self.file_1_uuid
        assert row_3_rights_statement.status == "ORIGINAL"
        assert row_3_rights_statement.rightsbasis == "Copyright"

        row_3_copyright_info = models.RightsStatementCopyright.objects.order_by("pk")[1]
        assert row_3_copyright_info.rightsstatement == row_3_rights_statement
        assert row_3_copyright_info.copyrightstatus == "cop status3"
        assert row_3_copyright_info.copyrightjurisdiction == "cop juris3"
        assert row_3_copyright_info.copyrightstatusdeterminationdate == "2001-01-01"
        assert row_3_copyright_info.copyrightapplicablestartdate == "2002-02-02"
        assert row_3_copyright_info.copyrightenddateopen is False
        assert row_3_copyright_info.copyrightapplicableenddate == "2003-03-03"

        row_3_copyright_identifier = (
            models.RightsStatementCopyrightDocumentationIdentifier.objects.order_by(
                "pk"
            )[1]
        )
        assert (
            row_3_copyright_identifier.copyrightdocumentationidentifiertype
            == "cop type3"
        )
        assert row_3_copyright_identifier.copyrightdocumentationidentifierrole is None

        row_3_copyright_note = models.RightsStatementCopyrightNote.objects.order_by(
            "pk"
        )[1]
        assert row_3_copyright_note.rightscopyright == row_3_copyright_info
        assert row_3_copyright_note.copyrightnote == "cop note 3"

        row_3_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[1]
        assert row_3_grant.rightsstatement == row_3_rights_statement
        assert row_3_grant.act == "cop act2"
        assert row_3_grant.startdate == "2004-04-04"
        assert row_3_grant.enddateopen is False
        assert row_3_grant.enddate == "2005-05-05"

        row_3_restriction = (
            models.RightsStatementRightsGrantedRestriction.objects.order_by("pk")[1]
        )
        assert row_3_restriction.rightsgranted == row_3_grant
        assert row_3_restriction.restriction == "Allow"

        row_3_grant_note = models.RightsStatementRightsGrantedNote.objects.order_by(
            "pk"
        )[1]
        assert row_3_grant_note.rightsgranted == row_3_grant
        assert row_3_grant_note.rightsgrantednote == "cop grant note3"

        # Test row 4
        row_4_rights_statement = models.RightsStatement.objects.order_by("pk")[2]
        assert (
            row_4_rights_statement.metadataappliestotype
            == self.get_metadata_applies_to_type_for_file()
        )
        assert row_4_rights_statement.metadataappliestoidentifier == self.file_1_uuid
        assert row_4_rights_statement.status == "ORIGINAL"
        assert row_4_rights_statement.rightsbasis == "License"

        row_4_license_info = models.RightsStatementLicense.objects.order_by("pk")[0]
        assert row_4_license_info.rightsstatement == row_4_rights_statement
        assert row_4_license_info.licenseterms == "lic terms"
        assert row_4_license_info.licenseapplicablestartdate == "1982-01-01"
        assert row_4_license_info.licenseenddateopen is False
        assert row_4_license_info.licenseapplicableenddate == "1983-02-02"

        row_4_license_identifier = (
            models.RightsStatementLicenseDocumentationIdentifier.objects.order_by("pk")[
                0
            ]
        )
        assert (
            row_4_license_identifier.licensedocumentationidentifiertype
            == "license type"
        )
        assert (
            row_4_license_identifier.licensedocumentationidentifiervalue
            == "license value"
        )
        assert row_4_license_identifier.licensedocumentationidentifierrole is None

        row_4_license_note = models.RightsStatementLicenseNote.objects.order_by("pk")[0]
        assert row_4_license_note.rightsstatementlicense == row_4_license_info
        assert row_4_license_note.licensenote == "lic note"

        row_4_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[2]
        assert row_4_grant.rightsstatement == row_4_rights_statement
        assert row_4_grant.act == "lic act"
        assert row_4_grant.startdate is None
        assert row_4_grant.enddateopen is False
        assert row_4_grant.enddate is None

        row_4_restriction = (
            models.RightsStatementRightsGrantedRestriction.objects.order_by("pk")[2]
        )
        assert row_4_restriction.rightsgranted == row_4_grant
        assert row_4_restriction.restriction == "Allow"

        # Test row 5
        row_5_rights_statement = models.RightsStatement.objects.order_by("pk")[3]
        assert (
            row_5_rights_statement.metadataappliestotype
            == self.get_metadata_applies_to_type_for_file()
        )
        assert row_5_rights_statement.metadataappliestoidentifier == self.file_1_uuid
        assert row_5_rights_statement.status == "ORIGINAL"
        assert row_5_rights_statement.rightsbasis == "Statute"

        row_5_statute_info = models.RightsStatementStatuteInformation.objects.order_by(
            "pk"
        )[0]
        assert row_5_statute_info.rightsstatement == row_5_rights_statement
        assert row_5_statute_info.statutejurisdiction == "stat juris"
        assert row_5_statute_info.statutedeterminationdate == "1972-02-02"
        assert row_5_statute_info.statutecitation == "stat cit"
        assert row_5_statute_info.statuteapplicablestartdate == "1966-01-01"
        assert row_5_statute_info.statuteenddateopen is True
        assert row_5_statute_info.statuteapplicableenddate is None

        row_5_statute_identifier = (
            models.RightsStatementStatuteDocumentationIdentifier.objects.order_by("pk")[
                0
            ]
        )
        assert (
            row_5_statute_identifier.statutedocumentationidentifiertype
            == "statute type"
        )
        assert (
            row_5_statute_identifier.statutedocumentationidentifiervalue
            == "statute value"
        )
        assert (
            row_5_statute_identifier.statutedocumentationidentifierrole
            == "statute role"
        )

        row_5_statute_note = (
            models.RightsStatementStatuteInformationNote.objects.order_by("pk")[0]
        )
        assert row_5_statute_note.rightsstatementstatute == row_5_statute_info
        assert row_5_statute_note.statutenote == "statute note"

        row_5_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[3]
        assert row_5_grant.rightsstatement == row_5_rights_statement
        assert row_5_grant.act == "stat act"
        assert row_5_grant.startdate is None
        assert row_5_grant.enddateopen is False
        assert row_5_grant.enddate is None

        row_5_restriction = (
            models.RightsStatementRightsGrantedRestriction.objects.order_by("pk")[3]
        )
        assert row_5_restriction.rightsgranted == row_5_grant
        assert row_5_restriction.restriction == "Allow"

        # Test row 6
        row_6_rights_statement = models.RightsStatement.objects.order_by("pk")[4]
        assert (
            row_6_rights_statement.metadataappliestotype
            == self.get_metadata_applies_to_type_for_file()
        )
        assert row_6_rights_statement.metadataappliestoidentifier == self.file_1_uuid
        assert row_6_rights_statement.status == "ORIGINAL"
        assert row_6_rights_statement.rightsbasis == "Other"

        row_6_other_info = (
            models.RightsStatementOtherRightsInformation.objects.order_by("pk")[0]
        )
        assert row_6_other_info.rightsstatement == row_6_rights_statement
        assert row_6_other_info.otherrightsbasis == "Other"
        assert row_6_other_info.otherrightsapplicablestartdate == "1945-01-01"
        assert row_6_other_info.otherrightsenddateopen is False
        assert row_6_other_info.otherrightsapplicableenddate == "1950-05-05"

        row_6_other_note = (
            models.RightsStatementOtherRightsInformationNote.objects.order_by("pk")[0]
        )
        assert row_6_other_note.rightsstatementotherrights == row_6_other_info
        assert row_6_other_note.otherrightsnote == "other note"

        row_6_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[4]
        assert row_6_grant.rightsstatement == row_6_rights_statement
        assert row_6_grant.act == "other act"
        assert row_6_grant.startdate == "1920-01-01"
        assert row_6_grant.enddateopen is False
        assert row_6_grant.enddate == "1921-01-01"

        row_6_restriction = (
            models.RightsStatementRightsGrantedRestriction.objects.order_by("pk")[4]
        )
        assert row_6_restriction.rightsgranted == row_6_grant
        assert row_6_restriction.restriction == "Allow"

        row_6_grant_note = models.RightsStatementRightsGrantedNote.objects.order_by(
            "pk"
        )[2]
        assert row_6_grant_note.rightsgranted == row_6_grant
        assert row_6_grant_note.rightsgrantednote == "other grant note"

        # Test row 7
        row_7_rights_statement = models.RightsStatement.objects.order_by("pk")[5]
        assert (
            row_7_rights_statement.metadataappliestotype
            == self.get_metadata_applies_to_type_for_file()
        )
        assert row_7_rights_statement.metadataappliestoidentifier == self.file_2_uuid
        assert row_7_rights_statement.status == "ORIGINAL"
        assert row_7_rights_statement.rightsbasis == "Donor"

        row_7_other_info = (
            models.RightsStatementOtherRightsInformation.objects.order_by("pk")[1]
        )
        assert row_7_other_info.rightsstatement == row_7_rights_statement
        assert row_7_other_info.otherrightsbasis == "Donor"
        assert row_7_other_info.otherrightsapplicablestartdate is None
        assert row_7_other_info.otherrightsenddateopen is False
        assert row_7_other_info.otherrightsapplicableenddate is None

        row_7_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[5]
        assert row_7_grant.rightsstatement == row_7_rights_statement
        assert row_7_grant.act == "donor act"
        assert row_7_grant.startdate is None
        assert row_7_grant.enddateopen is False
        assert row_7_grant.enddate is None

        # Test row 8
        row_8_rights_statement = models.RightsStatement.objects.order_by("pk")[6]
        assert (
            row_8_rights_statement.metadataappliestotype
            == self.get_metadata_applies_to_type_for_file()
        )
        assert row_8_rights_statement.metadataappliestoidentifier == self.file_2_uuid
        assert row_8_rights_statement.status == "ORIGINAL"
        assert row_8_rights_statement.rightsbasis == "Policy"

        row_8_other_info = (
            models.RightsStatementOtherRightsInformation.objects.order_by("pk")[2]
        )
        assert row_8_other_info.rightsstatement == row_8_rights_statement
        assert row_8_other_info.otherrightsbasis == "Policy"
        assert row_8_other_info.otherrightsapplicablestartdate is None
        assert row_8_other_info.otherrightsenddateopen is False
        assert row_8_other_info.otherrightsapplicableenddate is None

        row_8_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[6]
        assert row_8_grant.rightsstatement == row_8_rights_statement
        assert row_8_grant.act == "policy act"
        assert row_8_grant.startdate is None
        assert row_8_grant.enddateopen is False
        assert row_8_grant.enddate is None


class TestRightsImportFromCsvWithUnicode(TestRightsImportFromCsvBase):

    fixture_files = [
        "metadata_applies_to_type.json",
        "transfer.json",
        "files-transfer-unicode.json",
    ]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def test_rows_processed_and_database_content_with_unicode_filepath(self):
        """Test CSV import using the RightsReader class when file paths have unicode characters in them.

        It should process all rows of the CSV file even if file paths have unicode characters in them.
        It should populate the rights-related models using data from the CSV file.
        """
        models.File.objects.get(pk="47813453-6872-442b-9d65-6515be3c5aa1")

        rights_csv_filepath = os.path.join(
            THIS_DIR, "fixtures/rights-unicode-filepath.csv"
        )
        parser = rights_from_csv.RightCsvReader(
            Job("stub", "stub", []), self.transfer_uuid, u"%s" % rights_csv_filepath
        )
        rows_processed = parser.parse()

        assert rows_processed == 1

        # Test row 1
        row_1_rights_statement = models.RightsStatement.objects.order_by("pk")[0]
        assert (
            row_1_rights_statement.metadataappliestotype
            == self.get_metadata_applies_to_type_for_file()
        )
        assert row_1_rights_statement.metadataappliestoidentifier == self.file_1_uuid
        assert row_1_rights_statement.status == "ORIGINAL"
        assert row_1_rights_statement.rightsbasis == "Copyright"

        row_1_copyright_info = models.RightsStatementCopyright.objects.order_by("pk")[0]
        assert row_1_copyright_info.rightsstatement == row_1_rights_statement
        assert row_1_copyright_info.copyrightstatus == "cop status"
        assert row_1_copyright_info.copyrightjurisdiction == "cop juris"
        assert row_1_copyright_info.copyrightstatusdeterminationdate == "2001-01-01"
        assert row_1_copyright_info.copyrightapplicablestartdate == "2002-02-02"
        assert row_1_copyright_info.copyrightenddateopen is False
        assert row_1_copyright_info.copyrightapplicableenddate == "2003-03-03"

        row_1_copyright_identifier = (
            models.RightsStatementCopyrightDocumentationIdentifier.objects.order_by(
                "pk"
            )[0]
        )
        assert (
            row_1_copyright_identifier.copyrightdocumentationidentifiertype
            == "cop type"
        )
        assert (
            row_1_copyright_identifier.copyrightdocumentationidentifierrole
            == "cop role"
        )

        row_1_copyright_note = models.RightsStatementCopyrightNote.objects.order_by(
            "pk"
        )[0]
        assert row_1_copyright_note.rightscopyright == row_1_copyright_info
        assert row_1_copyright_note.copyrightnote == "cop note"

        row_1_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[0]
        assert row_1_grant.rightsstatement == row_1_rights_statement
        assert row_1_grant.act == "cop act"
        assert row_1_grant.startdate == "2004-04-04"
        assert row_1_grant.enddateopen is False
        assert row_1_grant.enddate == "2005-05-05"
