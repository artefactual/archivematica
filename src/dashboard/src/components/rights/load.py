# -*- coding: utf-8 -*-
"""Import ``PREMISRights``.

Similar to ``rights_from_csv`` in that it imports rights statements. In this
module, we load a ``premisrw.PREMISRights`` object into the database.

This module does not use the ``__`` notation for accessors offered by
``premisrw``.
"""
from __future__ import absolute_import, unicode_literals

import six

from components.helpers import get_metadata_type_id_by_description
from main.models import (
    File,
    Transfer,
    SIP,
    RightsStatement,
    RightsStatementCopyright,
    RightsStatementLicense,
    RightsStatementRightsGranted,
    RightsStatementStatuteInformation,
    RightsStatementOtherRightsInformation,
)


def load_rights(obj, rights):
    """Populate ``PREMISRights`` into the database."""
    return _create_rights_statement(_mdtype(obj), obj.uuid, rights.rights_statement[0])


def _create_rights_statement(md_type, obj_id, rights_statement):
    """Populate ``RightsStatement`` from a ``PREMISRights`` object."""
    db_stmt = RightsStatement.objects.create(
        metadataappliestotype=md_type,
        metadataappliestoidentifier=obj_id,
        status="ORIGINAL",
        rightsstatementidentifiertype=rights_statement.rights_statement_identifier_type,
        rightsstatementidentifiervalue=rights_statement.rights_statement_identifier_value,
        rightsbasis=rights_statement.rights_basis,
    )

    if db_stmt.rightsbasis == "Copyright":
        copyright_information = rights_statement.copyright_information[0]
        _create_rights_basis_copyright(db_stmt, copyright_information)
    elif db_stmt.rightsbasis == "License":
        license_information = rights_statement.license_information[0]
        _create_rights_basis_license(db_stmt, license_information)
    elif db_stmt.rightsbasis == "Statute":
        statute_information = rights_statement.statute_information[0]
        _create_rights_basis_statute(db_stmt, statute_information)
    elif db_stmt.rightsbasis in ("Donor", "Policy", "Other"):
        other_rights_information = rights_statement.other_rights_information[0]
        _create_rights_basis_other(db_stmt, other_rights_information)
    else:
        raise ValueError("Unsupported basis: {}".format(db_stmt.rightsbasis))

    for item in rights_statement.rights_granted:
        _create_rights_granted(db_stmt, item)

    return db_stmt


def _create_rights_basis_copyright(db_stmt, copyright_information):
    """Persist ``copyrightInformation``.

    <xs:complexType name="copyrightInformationComplexType">
        <xs:sequence>
            <xs:element ref="copyrightStatus"/>
            <xs:element ref="copyrightJurisdiction"/>
            <xs:element ref="copyrightStatusDeterminationDate" minOccurs="0"/>
            <xs:element ref="copyrightNote" minOccurs="0" maxOccurs="unbounded"/>
            <xs:element ref="copyrightDocumentationIdentifier" minOccurs="0" maxOccurs="unbounded"/>
            <xs:element ref="copyrightApplicableDates" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>
    """
    create_kwargs = {
        "rightsstatement": db_stmt,
        "copyrightstatus": copyright_information.copyright_status.lower(),
        "copyrightjurisdiction": copyright_information.copyright_jurisdiction,
    }
    create_kwargs.update(
        _get_dates(
            copyright_information,
            "copyright_applicable_dates",
            prefix="copyrightapplicable",
        )
    )
    create_kwargs.update(
        _get_simple_attr(
            copyright_information,
            "copyright_status_determination_date",
            "copyrightstatusdeterminationdate",
            modifier=_parse_edtf_datetime,
        )
    )

    ret = RightsStatementCopyright.objects.create(**create_kwargs)

    _set_list(
        copyright_information,
        "copyright_note",
        ret.rightsstatementcopyrightnote_set,
        "copyrightnote",
    )
    _set_list(
        copyright_information,
        "copyright_documentation_identifier",
        ret.rightsstatementcopyrightdocumentationidentifier_set,
        (
            (
                "copyrightdocumentationidentifiertype",
                "copyright_documentation_identifier_type",
            ),
            (
                "copyrightdocumentationidentifiervalue",
                "copyright_documentation_identifier_value",
            ),
            (
                "copyrightdocumentationidentifierrole",
                "copyright_documentation_identifier_role",
            ),
        ),
    )

    return ret


def _create_rights_basis_license(db_stmt, license_information):
    """Persist ``licenseInformation``.

    <xs:complexType name="licenseInformationComplexType">
        <xs:choice>
            <xs:sequence>
                <xs:element ref="licenseDocumentationIdentifier" maxOccurs="unbounded"/>
                <xs:element ref="licenseTerms" minOccurs="0"/>
                <xs:element ref="licenseNote" minOccurs="0" maxOccurs="unbounded"/>
                <xs:element ref="licenseApplicableDates" minOccurs="0"/>
            </xs:sequence>
            <xs:sequence>
                <xs:element ref="licenseTerms"/>
                <xs:element ref="licenseNote" minOccurs="0" maxOccurs="unbounded"/>
                <xs:element ref="licenseApplicableDates" minOccurs="0"/>
            </xs:sequence>
            <xs:sequence>
                <xs:element ref="licenseNote" maxOccurs="unbounded"/>
                <xs:element ref="licenseApplicableDates" minOccurs="0"/>
            </xs:sequence>
            <xs:element ref="licenseApplicableDates"/>
        </xs:choice>
    </xs:complexType>
    """
    create_kwargs = {"rightsstatement": db_stmt}
    create_kwargs.update(
        _get_dates(
            license_information, "license_applicable_dates", prefix="licenseapplicable"
        )
    )
    create_kwargs.update(
        _get_simple_attr(license_information, "license_terms", "licenseterms")
    )

    ret = RightsStatementLicense.objects.create(**create_kwargs)

    _set_list(
        license_information,
        "license_note",
        ret.rightsstatementlicensenote_set,
        "licensenote",
    )
    _set_list(
        license_information,
        "license_documentation_identifier",
        ret.rightsstatementlicensedocumentationidentifier_set,
        (
            (
                "licensedocumentationidentifiertype",
                "license_documentation_identifier_type",
            ),
            (
                "licensedocumentationidentifiervalue",
                "license_documentation_identifier_value",
            ),
            (
                "licensedocumentationidentifierrole",
                "license_documentation_identifier_role",
            ),
        ),
    )

    return ret


def _create_rights_basis_statute(db_stmt, statute_information):
    """Persist ``statuteInformation``.

    <xs:complexType name="statuteInformationComplexType">
        <xs:sequence>
            <xs:element ref="statuteJurisdiction"/>
            <xs:element ref="statuteCitation"/>
            <xs:element ref="statuteInformationDeterminationDate" minOccurs="0"/>
            <xs:element ref="statuteNote" minOccurs="0" maxOccurs="unbounded"/>
            <xs:element ref="statuteDocumentationIdentifier" minOccurs="0" maxOccurs="unbounded"/>
            <xs:element ref="statuteApplicableDates" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>
    """
    create_kwargs = {
        "rightsstatement": db_stmt,
        "statutejurisdiction": statute_information.statute_jurisdiction,
        "statutecitation": statute_information.statute_citation,
    }
    create_kwargs.update(
        _get_dates(
            statute_information, "statute_applicable_dates", prefix="statuteapplicable"
        )
    )
    create_kwargs.update(
        _get_simple_attr(
            statute_information,
            "statute_determination_date",
            "statutedeterminationdate",
            modifier=_parse_edtf_datetime,
        )
    )

    ret = RightsStatementStatuteInformation.objects.create(**create_kwargs)

    _set_list(
        statute_information,
        "statute_note",
        ret.rightsstatementstatuteinformationnote_set,
        "statutenote",
    )
    _set_list(
        statute_information,
        "statute_information_documentation_identifier",
        ret.rightsstatementstatutedocumentationidentifier_set,
        (
            (
                "statutedocumentationidentifiertype",
                "statute_information_documentation_identifier_type",
            ),
            (
                "statutedocumentationidentifiervalue",
                "statute_information_documentation_identifier_value",
            ),
            (
                "statutedocumentationidentifierrole",
                "statute_information_documentation_identifier_role",
            ),
        ),
    )

    return ret


def _create_rights_basis_other(db_stmt, other_rights):
    """Persist ``otherRightsInformation``.

    <xs:complexType name="otherRightsInformationComplexType">
        <xs:sequence>
            <xs:element ref="otherRightsDocumentationIdentifier" minOccurs="0" maxOccurs="unbounded"/>
            <xs:element ref="otherRightsBasis"/>
            <xs:element ref="otherRightsApplicableDates" minOccurs="0"/>
            <xs:element ref="otherRightsNote" minOccurs="0" maxOccurs="unbounded"/>
        </xs:sequence>
    </xs:complexType>
    """
    create_kwargs = {
        "rightsstatement": db_stmt,
        "otherrightsbasis": other_rights.other_rights_basis,
    }
    create_kwargs.update(
        _get_dates(
            other_rights,
            "other_rights_applicable_dates",
            prefix="otherrightsapplicable",
        )
    )

    ret = RightsStatementOtherRightsInformation.objects.create(**create_kwargs)

    _set_list(
        other_rights,
        "other_rights_note",
        ret.rightsstatementotherrightsinformationnote_set,
        "otherrightsnote",
    )
    _set_list(
        other_rights,
        "other_rights_documentation_identifier",
        ret.rightsstatementotherrightsdocumentationidentifier_set,
        (
            (
                "otherrightsdocumentationidentifiertype",
                "other_rights_documentation_identifier_type",
            ),
            (
                "otherrightsdocumentationidentifiervalue",
                "other_rights_documentation_identifier_value",
            ),
            (
                "otherrightsdocumentationidentifierrole",
                "other_rights_documentation_identifier_role",
            ),
        ),
    )

    return ret


def _create_rights_granted(db_stmt, rights_granted):
    """Persist ``rightsGranted``.

    <xs:complexType name="rightsGrantedComplexType">
        <xs:sequence>
            <xs:element ref="act"/>
            <xs:element ref="restriction" minOccurs="0" maxOccurs="unbounded"/>
            <xs:element ref="termOfGrant" minOccurs="0"/>
            <xs:element ref="termOfRestriction" minOccurs="0"/>
            <xs:element ref="rightsGrantedNote" minOccurs="0" maxOccurs="unbounded"/>
        </xs:sequence>
    </xs:complexType>
    """
    create_kwargs = {"rightsstatement": db_stmt, "act": rights_granted.act}
    create_kwargs.update(_get_dates(rights_granted, "term_of_grant"))

    ret = RightsStatementRightsGranted.objects.create(**create_kwargs)

    _set_list(rights_granted, "restriction", ret.restrictions, "restriction")
    _set_list(rights_granted, "rights_granted_note", ret.notes, "rightsgrantednote")

    return ret


_ALLOWED_METADATA_TYPES = (File, Transfer, SIP)


def _mdtype(obj):
    """Return the ``MetadataAppliesToType`` that corresponds to ``obj.``."""
    if obj.__class__ not in _ALLOWED_METADATA_TYPES:
        raise TypeError(
            "Types supported: %s"
            % ", ".join([item.__name__ for item in _ALLOWED_METADATA_TYPES])
        )
    return get_metadata_type_id_by_description(obj.__class__.__name__)


def _parse_edtf_datetime(date_string):
    if not date_string:
        return None
    return date_string.replace("-", "/")


def _get_dates(abctuple, attr, prefix=""):
    """Return dict with start-end-date attributes."""
    try:
        dates = getattr(abctuple, attr)[0]
    except (AttributeError, IndexError, TypeError):
        return {}

    startdate_key = "{}startdate".format(prefix)
    enddate_key = "{}enddate".format(prefix)

    suffix = "applicable"
    if prefix.endswith(suffix):
        prefix = prefix[: -len(suffix)]
    enddateopen_key = "{}enddateopen".format(prefix)

    ret = {}

    # Tuple when undefined, weird!
    if isinstance(dates.start_date, tuple) or not dates.start_date:
        return ret

    ret = {startdate_key: _parse_edtf_datetime(dates.start_date)}
    if dates.end_date == "OPEN":
        ret[enddateopen_key] = True
    elif dates.end_date:
        ret[enddate_key] = _parse_edtf_datetime(dates.end_date)

    return ret


def _set_list(abctuple, attr, relmanager, fkprops):
    """Create a related model given its ``RelatedManager`` (``relmanager``).

    - ``abctuple`` is the data source (``PREMISElement`` tuple)
    - ``attr`` is the list property that we are writing.
    - ``relmanager`` e.g. ``granted.restrictions``.
    - ``fkprops`` association of model properties and PREMIS properties
      e.g. "copyrightnote" or (("modelprop1", "tupleprop1",), ...)
    """
    try:
        values = getattr(abctuple, attr)
    except AttributeError:
        return
    if not isinstance(values, tuple):
        values = (values,)
    for item in values:
        if isinstance(fkprops, six.string_types):
            create_kwargs = {fkprops: item}
        else:
            create_kwargs = {k: getattr(item, v) for k, v in fkprops}
        relmanager.create(**create_kwargs)


def _get_simple_attr(abctuple, attr, prop, modifier=None):
    try:
        value = getattr(abctuple, attr)
    except AttributeError:
        return {}
    if not isinstance(value, six.string_types):
        raise TypeError("Expected string type")
    if modifier is not None:
        value = modifier(value)
    if not value:
        return {}
    return {prop: value}
