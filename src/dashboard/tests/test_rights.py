# -*- coding: utf-8 -*-
from __future__ import absolute_import

from metsrw.plugins import premisrw
import pytest
import uuid

from components.rights import load
from main.models import File, Transfer, SIP, MetadataAppliesToType


RIGHTS_STATEMENT_IDENTIFIER = (
    "rights_statement_identifier",
    ("rights_statement_identifier_type", "UUID"),
    ("rights_statement_identifier_value", "3a9838ac-ebe9-4ecb-ba46-c31ee1d6e7c2"),
)

RIGHTS_STATEMENT_COPYRIGHT = (
    ("rights_basis", "Copyright"),
    (
        "copyright_information",
        ("copyright_status", "Under copyright"),
        ("copyright_jurisdiction", "CA"),
        ("copyright_status_determination_date", "2015"),
        ("copyright_note", "Dummy note 1"),
        (
            "copyright_documentation_identifier",
            ("copyright_documentation_identifier_type", "UUID"),
            (
                "copyright_documentation_identifier_value",
                "a59b5006-23c4-4195-bc1e-7d1855d555cc",
            ),
            ("copyright_documentation_identifier_role", "role"),
        ),
        ("copyright_applicable_dates", ("start_date", "1999"), ("end_date", "OPEN")),
    ),
)

RIGHTS_STATEMENT_LICENSE = (
    ("rights_basis", "License"),
    (
        "license_information",
        (
            "license_documentation_identifier",
            ("license_documentation_identifier_type", "UUID"),
            (
                "license_documentation_identifier_value",
                "a59b5006-23c4-4195-bc1e-7d1855d555cc",
            ),
            ("license_documentation_identifier_role", "role"),
        ),
        ("license_terms", "Dummy license terms"),
        ("license_note", "Dummy note 1"),
        ("license_applicable_dates", ("start_date", "1999"), ("end_date", "OPEN")),
    ),
)

RIGHTS_STATEMENT_STATUTE = (
    ("rights_basis", "Statute"),
    (
        "statute_information",
        ("statute_jurisdiction", "Jurisdiction"),
        ("statute_citation", "Citation"),
        ("statute_determination_date", "2015"),
        ("statute_note", "Dummy note 1"),
        (
            "statute_information_documentation_identifier",
            ("statute_information_documentation_identifier_type", "UUID"),
            (
                "statute_information_documentation_identifier_value",
                "a59b5006-23c4-4195-bc1e-7d1855d555cc",
            ),
            ("statute_information_documentation_identifier_role", "role"),
        ),
        ("statute_applicable_dates", ("start_date", "1999"), ("end_date", "OPEN")),
    ),
)

RIGHTS_STATEMENT_OTHER = (
    ("rights_basis", "Other"),
    (
        "other_rights_information",
        (
            "other_rights_documentation_identifier",
            ("other_rights_documentation_identifier_type", "UUID"),
            (
                "other_rights_documentation_identifier_value",
                "a59b5006-23c4-4195-bc1e-7d1855d555cc",
            ),
            ("other_rights_documentation_identifier_role", "role"),
        ),
        ("other_rights_basis", "Foobar"),
        ("other_rights_applicable_dates", ("start_date", "1999"), ("end_date", "OPEN")),
        ("other_rights_note", "Dummy note 1"),
    ),
)

RIGHTS_STATEMENT_GRANTED_1 = (
    "rights_granted",
    ("act", "Disseminate"),
    ("restriction", "Allow"),
    ("term_of_grant", ("start_date", "2000"), ("end_date", "OPEN")),
    ("rights_granted_note", "Attribution required"),
)

RIGHTS_STATEMENT_GRANTED_2 = (
    "rights_granted",
    ("act", "Access"),
    ("restriction", "Allow"),
    ("term_of_grant", ("start_date", "1999"), ("end_date", "OPEN")),
    ("rights_granted_note", "Access one year before dissemination"),
)

RIGHTS_STATEMENT_LINKING_OBJECT_IDENTIFIER = (
    "linking_object_identifier",
    ("linking_object_identifier_type", "UUID"),
    ("linking_object_identifier_value", "c09903c4-bc29-4db4-92da-47355eec752f"),
)


@pytest.fixture()
def rights_statement_with_basis_copyright():
    rights_statement = (
        "rights_statement",
        RIGHTS_STATEMENT_IDENTIFIER,
        RIGHTS_STATEMENT_COPYRIGHT[0],
        RIGHTS_STATEMENT_COPYRIGHT[1],
        RIGHTS_STATEMENT_GRANTED_1,
        RIGHTS_STATEMENT_GRANTED_2,
        RIGHTS_STATEMENT_LINKING_OBJECT_IDENTIFIER,
    )
    return premisrw.PREMISRights(
        data=("rights", premisrw.PREMIS_META, rights_statement)
    )


@pytest.fixture()
def rights_statement_with_basis_license():
    rights_statement = (
        "rights_statement",
        RIGHTS_STATEMENT_IDENTIFIER,
        RIGHTS_STATEMENT_LICENSE[0],
        RIGHTS_STATEMENT_LICENSE[1],
        RIGHTS_STATEMENT_GRANTED_1,
        RIGHTS_STATEMENT_GRANTED_2,
        RIGHTS_STATEMENT_LINKING_OBJECT_IDENTIFIER,
    )
    return premisrw.PREMISRights(
        data=("rights", premisrw.PREMIS_META, rights_statement)
    )


@pytest.fixture()
def rights_statement_with_basis_statute():
    rights_statement = (
        "rights_statement",
        RIGHTS_STATEMENT_IDENTIFIER,
        RIGHTS_STATEMENT_STATUTE[0],
        RIGHTS_STATEMENT_STATUTE[1],
        RIGHTS_STATEMENT_GRANTED_1,
        RIGHTS_STATEMENT_GRANTED_2,
        RIGHTS_STATEMENT_LINKING_OBJECT_IDENTIFIER,
    )
    return premisrw.PREMISRights(
        data=("rights", premisrw.PREMIS_META, rights_statement)
    )


@pytest.fixture()
def rights_statement_with_basis_other():
    rights_statement = (
        "rights_statement",
        RIGHTS_STATEMENT_IDENTIFIER,
        RIGHTS_STATEMENT_OTHER[0],
        RIGHTS_STATEMENT_OTHER[1],
        RIGHTS_STATEMENT_GRANTED_1,
        RIGHTS_STATEMENT_GRANTED_2,
        RIGHTS_STATEMENT_LINKING_OBJECT_IDENTIFIER,
    )
    return premisrw.PREMISRights(
        data=("rights", premisrw.PREMIS_META, rights_statement)
    )


@pytest.fixture()
def file(db):
    return File.objects.create(uuid=uuid.uuid4())


@pytest.mark.django_db
def test_mdtype():
    assert isinstance(load._mdtype(File()), MetadataAppliesToType)
    assert isinstance(load._mdtype(Transfer()), MetadataAppliesToType)
    assert isinstance(load._mdtype(SIP()), MetadataAppliesToType)

    class UnknownClass(object):
        pass

    with pytest.raises(TypeError) as excinfo:
        load._mdtype(UnknownClass())
    assert "Types supported: File, Transfer, SIP" in str(excinfo.value)


@pytest.mark.django_db
def test_load_rights(file, rights_statement_with_basis_copyright):
    stmt = load.load_rights(file, rights_statement_with_basis_copyright)
    assert stmt.metadataappliestotype.description == "File"
    assert stmt.metadataappliestoidentifier == file.uuid
    assert stmt.rightsstatementidentifiertype == "UUID"
    assert stmt.rightsstatementidentifiervalue == "3a9838ac-ebe9-4ecb-ba46-c31ee1d6e7c2"

    rights_granted = stmt.rightsstatementrightsgranted_set.all()
    assert len(rights_granted) == 2
    assert rights_granted[0].act == "Disseminate"
    assert rights_granted[0].restrictions.all()[0].restriction == "Allow"
    assert rights_granted[0].notes.all()[0].rightsgrantednote == "Attribution required"
    assert rights_granted[0].startdate == "2000"
    assert rights_granted[0].enddate is None
    assert rights_granted[0].enddateopen is True
    assert rights_granted[1].act == "Access"
    assert rights_granted[1].restrictions.all()[0].restriction == "Allow"
    assert (
        rights_granted[1].notes.all()[0].rightsgrantednote
        == "Access one year before dissemination"
    )
    assert rights_granted[1].startdate == "1999"
    assert rights_granted[1].enddate is None
    assert rights_granted[1].enddateopen is True


@pytest.mark.django_db
def test_load_rights_with_basis_copyright(file, rights_statement_with_basis_copyright):
    stmt = load.load_rights(file, rights_statement_with_basis_copyright)

    assert stmt.rightsbasis == "Copyright"
    copyrights = stmt.rightsstatementcopyright_set.all()
    assert len(copyrights) == 1
    assert copyrights[0].copyrightstatus == "under copyright"
    assert copyrights[0].copyrightjurisdiction == "CA"
    assert copyrights[0].copyrightstatusdeterminationdate == "2015"
    assert (
        copyrights[0].rightsstatementcopyrightnote_set.all()[0].copyrightnote
        == "Dummy note 1"
    )
    assert (
        copyrights[0]
        .rightsstatementcopyrightdocumentationidentifier_set.all()[0]
        .copyrightdocumentationidentifiertype
        == "UUID"
    )
    assert (
        copyrights[0]
        .rightsstatementcopyrightdocumentationidentifier_set.all()[0]
        .copyrightdocumentationidentifiervalue
        == "a59b5006-23c4-4195-bc1e-7d1855d555cc"
    )
    assert (
        copyrights[0]
        .rightsstatementcopyrightdocumentationidentifier_set.all()[0]
        .copyrightdocumentationidentifierrole
        == "role"
    )


@pytest.mark.django_db
def test_load_rights_with_basis_license(file, rights_statement_with_basis_license):
    stmt = load.load_rights(file, rights_statement_with_basis_license)

    assert stmt.rightsbasis == "License"
    license = stmt.rightsstatementlicense_set.all()
    assert len(license) == 1
    assert license[0].licenseterms == "Dummy license terms"
    assert (
        license[0].rightsstatementlicensenote_set.all()[0].licensenote == "Dummy note 1"
    )
    assert (
        license[0]
        .rightsstatementlicensedocumentationidentifier_set.all()[0]
        .licensedocumentationidentifiertype
        == "UUID"
    )
    assert (
        license[0]
        .rightsstatementlicensedocumentationidentifier_set.all()[0]
        .licensedocumentationidentifiervalue
        == "a59b5006-23c4-4195-bc1e-7d1855d555cc"
    )
    assert (
        license[0]
        .rightsstatementlicensedocumentationidentifier_set.all()[0]
        .licensedocumentationidentifierrole
        == "role"
    )


@pytest.mark.django_db
def test_load_rights_with_basis_statute(file, rights_statement_with_basis_statute):
    stmt = load.load_rights(file, rights_statement_with_basis_statute)

    assert stmt.rightsbasis == "Statute"
    statute = stmt.rightsstatementstatuteinformation_set.all()
    assert len(statute) == 1
    assert statute[0].statutejurisdiction == "Jurisdiction"
    assert statute[0].statutecitation == "Citation"
    assert statute[0].statutedeterminationdate == "2015"
    assert (
        statute[0].rightsstatementstatuteinformationnote_set.all()[0].statutenote
        == "Dummy note 1"
    )
    assert (
        statute[0]
        .rightsstatementstatutedocumentationidentifier_set.all()[0]
        .statutedocumentationidentifiertype
        == "UUID"
    )
    assert (
        statute[0]
        .rightsstatementstatutedocumentationidentifier_set.all()[0]
        .statutedocumentationidentifiervalue
        == "a59b5006-23c4-4195-bc1e-7d1855d555cc"
    )
    assert (
        statute[0]
        .rightsstatementstatutedocumentationidentifier_set.all()[0]
        .statutedocumentationidentifierrole
        == "role"
    )


@pytest.mark.django_db
def test_load_rights_with_basis_other(file, rights_statement_with_basis_other):
    stmt = load.load_rights(file, rights_statement_with_basis_other)

    assert stmt.rightsbasis == "Other"
    otherrights = stmt.rightsstatementotherrightsinformation_set.all()
    assert len(otherrights) == 1
    assert otherrights[0].otherrightsbasis == "Foobar"
    assert (
        otherrights[0]
        .rightsstatementotherrightsinformationnote_set.all()[0]
        .otherrightsnote
        == "Dummy note 1"
    )
    assert (
        otherrights[0]
        .rightsstatementotherrightsdocumentationidentifier_set.all()[0]
        .otherrightsdocumentationidentifiertype
        == "UUID"
    )
    assert (
        otherrights[0]
        .rightsstatementotherrightsdocumentationidentifier_set.all()[0]
        .otherrightsdocumentationidentifiervalue
        == "a59b5006-23c4-4195-bc1e-7d1855d555cc"
    )
    assert (
        otherrights[0]
        .rightsstatementotherrightsdocumentationidentifier_set.all()[0]
        .otherrightsdocumentationidentifierrole
        == "role"
    )
