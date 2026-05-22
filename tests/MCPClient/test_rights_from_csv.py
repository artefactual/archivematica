import pathlib
from typing import Protocol
from typing import cast

import pytest

from archivematica.dashboard.main import models
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import rights_from_csv

THIS_DIR = pathlib.Path(__file__).parent
FILE_1_UUID = "47813453-6872-442b-9d65-6515be3c5aa1"
FILE_2_UUID = "60e5c61b-14ef-4e92-89ec-9b9201e68adb"


class _RightCsvReader(Protocol):
    def parse(self) -> int: ...


class _RightCsvReaderFactory(Protocol):
    def __call__(
        self,
        job: Job,
        transfer_uuid: str,
        rights_csv_filepath: str,
    ) -> _RightCsvReader: ...


@pytest.fixture
def file_metadata_applies_to_type() -> models.MetadataAppliesToType:
    metadata_type = models.MetadataAppliesToType.objects.filter(
        description="File"
    ).first()
    if metadata_type is not None:
        return metadata_type

    return models.MetadataAppliesToType.objects.create(
        id=models.MetadataAppliesToType.FILE_TYPE,
        description="File",
    )


def _create_transfer_file(
    transfer: models.Transfer,
    file_uuid: str,
    path: str,
    *,
    checksum: str = "",
    checksumtype: str = "",
    size: int = 18324,
) -> models.File:
    location = f"%transferDirectory%{path}".encode()
    return models.File.objects.create(
        uuid=file_uuid,
        transfer=transfer,
        filegrpuse="original",
        checksum=checksum,
        checksumtype=checksumtype,
        originallocation=location,
        currentlocation=location,
        size=size,
    )


def _assert_rights_statement_applies_to_file(
    rights_statement: models.RightsStatement,
    metadata_type: models.MetadataAppliesToType,
    file_uuid: str,
) -> None:
    assert metadata_type.description == "File"
    assert (
        rights_statement.metadataappliestotype.description == metadata_type.description
    )
    assert rights_statement.metadataappliestoidentifier == file_uuid


def _parse_rights_csv(
    job: Job,
    transfer_uuid: str,
    rights_csv_filepath: str,
) -> int:
    reader_factory = cast(_RightCsvReaderFactory, rights_from_csv.RightCsvReader)
    return reader_factory(job, transfer_uuid, rights_csv_filepath).parse()


def _write_file_basis_rights_csv(path: pathlib.Path, file_paths: list[str]) -> None:
    rows = "\n".join(f"{file_path},copyright" for file_path in file_paths)
    path.write_text(
        f"file,basis\n{rows}\n",
        encoding="utf-8",
    )


@pytest.fixture
def rights_transfer_files(transfer: models.Transfer) -> tuple[models.File, models.File]:
    return (
        _create_transfer_file(
            transfer,
            FILE_1_UUID,
            "objects/G31DS.TIF",
            size=125968,
        ),
        _create_transfer_file(transfer, FILE_2_UUID, "objects/lion.svg"),
    )


@pytest.fixture
def unicode_transfer_file(transfer: models.Transfer) -> models.File:
    return _create_transfer_file(
        transfer,
        FILE_1_UUID,
        "objects/たくさん directories/need name change/checking here/evélyn's photo.jpg",
        checksum="d2bed92b73c7090bb30a0b30016882e7069c437488e1513e9deaacbe29d38d92",
        checksumtype="sha256",
        size=158131,
    )


@pytest.mark.django_db
def test_rows_processed_and_database_content(
    mcp_job: Job,
    transfer: models.Transfer,
    file_metadata_applies_to_type: models.MetadataAppliesToType,
    rights_transfer_files: tuple[models.File, models.File],
) -> None:
    """Test CSV import using the RightsReader class.

    It should process valid rows of the CSV file.
    It should skip the third row data as basis/act is duplicate of earlier row.
    It should populate the rights-related models using data from the CSV file.
    """
    rights_csv_filepath = str(THIS_DIR / "fixtures" / "rights.csv")
    rows_processed = _parse_rights_csv(
        mcp_job,
        str(transfer.uuid),
        rights_csv_filepath,
    )

    # Test rows processed and model intance counts
    assert rows_processed == 9
    assert (
        models.RightsStatement.objects.count() == 8
    )  # One row in fixture CSV skipped due to duplicate basis/act combination
    assert models.RightsStatementLicense.objects.count() == 1
    assert models.RightsStatementCopyright.objects.count() == 2
    assert models.RightsStatementStatuteInformation.objects.count() == 1
    assert models.RightsStatementOtherRightsInformation.objects.count() == 4
    assert models.RightsStatementCopyrightDocumentationIdentifier.objects.count() == 2
    assert models.RightsStatementCopyrightNote.objects.count() == 2
    assert models.RightsStatementLicenseDocumentationIdentifier.objects.count() == 1
    assert models.RightsStatementLicenseNote.objects.count() == 1
    assert models.RightsStatementStatuteDocumentationIdentifier.objects.count() == 1
    assert models.RightsStatementStatuteInformationNote.objects.count() == 1
    assert (
        models.RightsStatementOtherRightsDocumentationIdentifier.objects.count() == 0
    )  # Not created as all related columns are blank
    assert models.RightsStatementOtherRightsInformationNote.objects.count() == 1
    assert models.RightsStatementRightsGranted.objects.count() == 7
    assert models.RightsStatementRightsGrantedRestriction.objects.count() == 5
    assert models.RightsStatementRightsGrantedNote.objects.count() == 3

    # Test row 1
    row_1_rights_statement = models.RightsStatement.objects.order_by("pk")[0]
    _assert_rights_statement_applies_to_file(
        row_1_rights_statement,
        file_metadata_applies_to_type,
        FILE_1_UUID,
    )
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
        models.RightsStatementCopyrightDocumentationIdentifier.objects.order_by("pk")[0]
    )
    assert row_1_copyright_identifier.copyrightdocumentationidentifiertype == "cop type"
    assert row_1_copyright_identifier.copyrightdocumentationidentifierrole == "cop role"

    row_1_copyright_note = models.RightsStatementCopyrightNote.objects.order_by("pk")[0]
    assert row_1_copyright_note.rightscopyright == row_1_copyright_info
    assert row_1_copyright_note.copyrightnote == "cop note"

    row_1_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[0]
    assert row_1_grant.rightsstatement == row_1_rights_statement
    assert row_1_grant.act == "cop act"
    assert row_1_grant.startdate == "2004-04-04"
    assert row_1_grant.enddateopen is False
    assert row_1_grant.enddate == "2005-05-05"

    row_1_restriction = models.RightsStatementRightsGrantedRestriction.objects.order_by(
        "pk"
    )[0]
    assert row_1_restriction.rightsgranted == row_1_grant
    assert row_1_restriction.restriction == "Allow"

    row_1_grant_note = models.RightsStatementRightsGrantedNote.objects.order_by("pk")[0]
    assert row_1_grant_note.rightsgranted == row_1_grant
    assert row_1_grant_note.rightsgrantednote == "cop grant note"

    # Test row 3 (row 2 is skipped as it has the same act and basis as a previous right for the file)
    row_3_rights_statement = models.RightsStatement.objects.order_by("pk")[1]
    _assert_rights_statement_applies_to_file(
        row_3_rights_statement,
        file_metadata_applies_to_type,
        FILE_1_UUID,
    )
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
        models.RightsStatementCopyrightDocumentationIdentifier.objects.order_by("pk")[1]
    )
    assert (
        row_3_copyright_identifier.copyrightdocumentationidentifiertype == "cop type3"
    )
    assert row_3_copyright_identifier.copyrightdocumentationidentifierrole is None

    row_3_copyright_note = models.RightsStatementCopyrightNote.objects.order_by("pk")[1]
    assert row_3_copyright_note.rightscopyright == row_3_copyright_info
    assert row_3_copyright_note.copyrightnote == "cop note 3"

    row_3_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[1]
    assert row_3_grant.rightsstatement == row_3_rights_statement
    assert row_3_grant.act == "cop act2"
    assert row_3_grant.startdate == "2004-04-04"
    assert row_3_grant.enddateopen is False
    assert row_3_grant.enddate == "2005-05-05"

    row_3_restriction = models.RightsStatementRightsGrantedRestriction.objects.order_by(
        "pk"
    )[1]
    assert row_3_restriction.rightsgranted == row_3_grant
    assert row_3_restriction.restriction == "Allow"

    row_3_grant_note = models.RightsStatementRightsGrantedNote.objects.order_by("pk")[1]
    assert row_3_grant_note.rightsgranted == row_3_grant
    assert row_3_grant_note.rightsgrantednote == "cop grant note3"

    # Test row 4
    row_4_rights_statement = models.RightsStatement.objects.order_by("pk")[2]
    _assert_rights_statement_applies_to_file(
        row_4_rights_statement,
        file_metadata_applies_to_type,
        FILE_1_UUID,
    )
    assert row_4_rights_statement.status == "ORIGINAL"
    assert row_4_rights_statement.rightsbasis == "License"

    row_4_license_info = models.RightsStatementLicense.objects.order_by("pk")[0]
    assert row_4_license_info.rightsstatement == row_4_rights_statement
    assert row_4_license_info.licenseterms == "lic terms"
    assert row_4_license_info.licenseapplicablestartdate == "1982-01-01"
    assert row_4_license_info.licenseenddateopen is False
    assert row_4_license_info.licenseapplicableenddate == "1983-02-02"

    row_4_license_identifier = (
        models.RightsStatementLicenseDocumentationIdentifier.objects.order_by("pk")[0]
    )
    assert row_4_license_identifier.licensedocumentationidentifiertype == "license type"
    assert (
        row_4_license_identifier.licensedocumentationidentifiervalue == "license value"
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

    row_4_restriction = models.RightsStatementRightsGrantedRestriction.objects.order_by(
        "pk"
    )[2]
    assert row_4_restriction.rightsgranted == row_4_grant
    assert row_4_restriction.restriction == "Allow"

    # Test row 5
    row_5_rights_statement = models.RightsStatement.objects.order_by("pk")[3]
    _assert_rights_statement_applies_to_file(
        row_5_rights_statement,
        file_metadata_applies_to_type,
        FILE_1_UUID,
    )
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
        models.RightsStatementStatuteDocumentationIdentifier.objects.order_by("pk")[0]
    )
    assert row_5_statute_identifier.statutedocumentationidentifiertype == "statute type"
    assert (
        row_5_statute_identifier.statutedocumentationidentifiervalue == "statute value"
    )
    assert row_5_statute_identifier.statutedocumentationidentifierrole == "statute role"

    row_5_statute_note = models.RightsStatementStatuteInformationNote.objects.order_by(
        "pk"
    )[0]
    assert row_5_statute_note.rightsstatementstatute == row_5_statute_info
    assert row_5_statute_note.statutenote == "statute note"

    row_5_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[3]
    assert row_5_grant.rightsstatement == row_5_rights_statement
    assert row_5_grant.act == "stat act"
    assert row_5_grant.startdate is None
    assert row_5_grant.enddateopen is False
    assert row_5_grant.enddate is None

    row_5_restriction = models.RightsStatementRightsGrantedRestriction.objects.order_by(
        "pk"
    )[3]
    assert row_5_restriction.rightsgranted == row_5_grant
    assert row_5_restriction.restriction == "Allow"

    # Test row 6
    row_6_rights_statement = models.RightsStatement.objects.order_by("pk")[4]
    _assert_rights_statement_applies_to_file(
        row_6_rights_statement,
        file_metadata_applies_to_type,
        FILE_1_UUID,
    )
    assert row_6_rights_statement.status == "ORIGINAL"
    assert row_6_rights_statement.rightsbasis == "Other"

    row_6_other_info = models.RightsStatementOtherRightsInformation.objects.order_by(
        "pk"
    )[0]
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

    row_6_restriction = models.RightsStatementRightsGrantedRestriction.objects.order_by(
        "pk"
    )[4]
    assert row_6_restriction.rightsgranted == row_6_grant
    assert row_6_restriction.restriction == "Allow"

    row_6_grant_note = models.RightsStatementRightsGrantedNote.objects.order_by("pk")[2]
    assert row_6_grant_note.rightsgranted == row_6_grant
    assert row_6_grant_note.rightsgrantednote == "other grant note"

    # Test row 7
    row_7_rights_statement = models.RightsStatement.objects.order_by("pk")[5]
    _assert_rights_statement_applies_to_file(
        row_7_rights_statement,
        file_metadata_applies_to_type,
        FILE_2_UUID,
    )
    assert row_7_rights_statement.status == "ORIGINAL"
    assert row_7_rights_statement.rightsbasis == "Donor"

    row_7_other_info = models.RightsStatementOtherRightsInformation.objects.order_by(
        "pk"
    )[1]
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
    _assert_rights_statement_applies_to_file(
        row_8_rights_statement,
        file_metadata_applies_to_type,
        FILE_2_UUID,
    )
    assert row_8_rights_statement.status == "ORIGINAL"
    assert row_8_rights_statement.rightsbasis == "Policy"

    row_8_other_info = models.RightsStatementOtherRightsInformation.objects.order_by(
        "pk"
    )[2]
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


@pytest.mark.django_db
def test_missing_transfer_files_in_csv_raise_file_error(
    mcp_job: Job,
    transfer: models.Transfer,
    file_metadata_applies_to_type: models.MetadataAppliesToType,
    rights_transfer_files: tuple[models.File, models.File],
    tmp_path: pathlib.Path,
) -> None:
    existing_file_path = "objects/G31DS.TIF"
    missing_file_paths = [
        "objects/missing-file-1.tif",
        "objects/missing-file-2.tif",
    ]
    rights_csv_filepath = tmp_path / "rights.csv"
    _write_file_basis_rights_csv(
        rights_csv_filepath,
        [existing_file_path, *missing_file_paths],
    )

    with pytest.raises(rights_from_csv.MissingTransferFilesException) as exc_info:
        _parse_rights_csv(
            mcp_job,
            str(transfer.uuid),
            str(rights_csv_filepath),
        )

    message = str(exc_info.value)
    assert "Files listed in rights.csv were not found in the transfer" in message
    assert f"transfer UUID: {transfer.uuid}" in message
    assert f"[Row 2] %transferDirectory%{existing_file_path}" not in message
    assert f"[Row 3] %transferDirectory%{missing_file_paths[0]}" in message
    assert f"[Row 4] %transferDirectory%{missing_file_paths[1]}" in message
    assert models.RightsStatement.objects.count() == 0


@pytest.mark.django_db
def test_rows_processed_and_database_content_with_unicode_filepath(
    mcp_job: Job,
    transfer: models.Transfer,
    file_metadata_applies_to_type: models.MetadataAppliesToType,
    unicode_transfer_file: models.File,
) -> None:
    """Test CSV import using the RightsReader class when file paths have unicode characters in them.

    It should process all rows of the CSV file even if file paths have unicode characters in them.
    It should populate the rights-related models using data from the CSV file.
    """
    models.File.objects.get(pk=FILE_1_UUID)

    rights_csv_filepath = str(THIS_DIR / "fixtures" / "rights-unicode-filepath.csv")
    rows_processed = _parse_rights_csv(
        mcp_job,
        str(transfer.uuid),
        rights_csv_filepath,
    )

    assert rows_processed == 1

    # Test row 1
    row_1_rights_statement = models.RightsStatement.objects.order_by("pk")[0]
    _assert_rights_statement_applies_to_file(
        row_1_rights_statement,
        file_metadata_applies_to_type,
        FILE_1_UUID,
    )
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
        models.RightsStatementCopyrightDocumentationIdentifier.objects.order_by("pk")[0]
    )
    assert row_1_copyright_identifier.copyrightdocumentationidentifiertype == "cop type"
    assert row_1_copyright_identifier.copyrightdocumentationidentifierrole == "cop role"

    row_1_copyright_note = models.RightsStatementCopyrightNote.objects.order_by("pk")[0]
    assert row_1_copyright_note.rightscopyright == row_1_copyright_info
    assert row_1_copyright_note.copyrightnote == "cop note"

    row_1_grant = models.RightsStatementRightsGranted.objects.order_by("pk")[0]
    assert row_1_grant.rightsstatement == row_1_rights_statement
    assert row_1_grant.act == "cop act"
    assert row_1_grant.startdate == "2004-04-04"
    assert row_1_grant.enddateopen is False
    assert row_1_grant.enddate == "2005-05-05"
