#!/usr/bin/env python2
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

# /src/dashboard/src/main/models.py

import sys
import uuid
import lxml.etree as etree

# dashboard
from main.models import RightsStatement

# archivematicaCommon
from countryCodes import getCodeForCountry
import namespaces as ns

RIGHTS_BASIS_OTHER = ["Policy", "Donor"]


def formatDate(date):
    """hack fix for 0.8, easy dashboard insertion ISO 8601 -> edtfSimpleType"""
    if date:
        date = date.replace("/", "-")
    return date


def _add_start_end_date_complex_type(name, elem, start_date, end_date, end_date_open):
    """Add new ``startAndEndDateComplexType`` subelement to ``elem``.

    The following elements in PREMIS use it:

      - ``copyrightApplicableDates``
      - ``licenseApplicableDates``
      - ``otherRightsApplicableDates``
      - ``statuteApplicableDates``
      - ``termOfGrant``
      - ``termOfRestriction``

    """
    if not any([start_date, end_date, end_date_open]):
        return
    dates = etree.SubElement(elem, ns.premisBNS + name)
    etree.SubElement(dates, ns.premisBNS + "startDate").text = (
        formatDate(start_date) if start_date else ""
    )
    end_date = "OPEN" if end_date_open else formatDate(end_date)
    if end_date:
        etree.SubElement(dates, ns.premisBNS + "endDate").text = end_date


def archivematicaGetRights(job, metadataAppliesToList, fileUUID, state):
    """[(fileUUID, fileUUIDTYPE), (sipUUID, sipUUIDTYPE), (transferUUID, transferUUIDType)]"""
    ret = []
    for metadataAppliesToidentifier, metadataAppliesToType in metadataAppliesToList:
        statements = RightsStatement.objects.filter(
            metadataappliestoidentifier=metadataAppliesToidentifier,
            metadataappliestotype_id=metadataAppliesToType,
        )
        for statement in statements:
            rightsStatement = createRightsStatement(job, statement, fileUUID, state)
            ret.append(rightsStatement)
    return ret


def createRightsStatement(job, statement, fileUUID, state):
    rightsStatement = etree.Element(
        ns.premisBNS + "rightsStatement", nsmap={"premis": ns.premisNS}
    )
    rightsStatement.set(
        ns.xsiBNS + "schemaLocation",
        ns.premisNS + " http://www.loc.gov/standards/premis/v3/premis.xsd",
    )

    # rightsStatement.set("version", "2.1") # cvc-complex-type.3.2.2: Attribute 'version' is not allowed to appear in element 'rightsStatement'.

    rightsStatementIdentifier = etree.SubElement(
        rightsStatement, ns.premisBNS + "rightsStatementIdentifier"
    )
    if statement.rightsstatementidentifiervalue:
        etree.SubElement(
            rightsStatementIdentifier, ns.premisBNS + "rightsStatementIdentifierType"
        ).text = statement.rightsstatementidentifiertype
        etree.SubElement(
            rightsStatementIdentifier, ns.premisBNS + "rightsStatementIdentifierValue"
        ).text = statement.rightsstatementidentifiervalue
    else:
        etree.SubElement(
            rightsStatementIdentifier, ns.premisBNS + "rightsStatementIdentifierType"
        ).text = "UUID"
        etree.SubElement(
            rightsStatementIdentifier, ns.premisBNS + "rightsStatementIdentifierValue"
        ).text = uuid.uuid4().__str__()
    if statement.rightsbasis in RIGHTS_BASIS_OTHER:
        etree.SubElement(rightsStatement, ns.premisBNS + "rightsBasis").text = "Other"
    else:
        etree.SubElement(
            rightsStatement, ns.premisBNS + "rightsBasis"
        ).text = statement.rightsbasis

    # Copyright information
    if statement.rightsbasis.lower() in ["copyright"]:
        for copyright in statement.rightsstatementcopyright_set.all():
            copyrightInformation = etree.SubElement(
                rightsStatement, ns.premisBNS + "copyrightInformation"
            )
            etree.SubElement(
                copyrightInformation, ns.premisBNS + "copyrightStatus"
            ).text = copyright.copyrightstatus
            copyrightJurisdiction = copyright.copyrightjurisdiction
            copyrightJurisdictionCode = getCodeForCountry(
                copyrightJurisdiction.__str__().upper()
            )
            if copyrightJurisdictionCode is not None:
                copyrightJurisdiction = copyrightJurisdictionCode
            etree.SubElement(
                copyrightInformation, ns.premisBNS + "copyrightJurisdiction"
            ).text = copyrightJurisdiction
            etree.SubElement(
                copyrightInformation, ns.premisBNS + "copyrightStatusDeterminationDate"
            ).text = formatDate(copyright.copyrightstatusdeterminationdate)
            # copyrightNote Repeatable
            for note in copyright.rightsstatementcopyrightnote_set.all():
                etree.SubElement(
                    copyrightInformation, ns.premisBNS + "copyrightNote"
                ).text = note.copyrightnote

            # RightsStatementCopyrightDocumentationIdentifier
            getDocumentationIdentifier(copyright, copyrightInformation)

            _add_start_end_date_complex_type(
                "copyrightApplicableDates",
                copyrightInformation,
                copyright.copyrightapplicablestartdate,
                copyright.copyrightapplicableenddate,
                copyright.copyrightenddateopen,
            )

    elif statement.rightsbasis.lower() in ["license"]:
        for license in statement.rightsstatementlicense_set.all():
            licenseInformation = etree.SubElement(
                rightsStatement, ns.premisBNS + "licenseInformation"
            )

            for (
                identifier
            ) in license.rightsstatementlicensedocumentationidentifier_set.all():

                licenseDocumentIdentifier = etree.SubElement(
                    licenseInformation, ns.premisBNS + "licenseDocumentationIdentifier"
                )
                etree.SubElement(
                    licenseDocumentIdentifier,
                    ns.premisBNS + "licenseDocumentationIdentifierType",
                ).text = identifier.licensedocumentationidentifiertype
                etree.SubElement(
                    licenseDocumentIdentifier,
                    ns.premisBNS + "licenseDocumentationIdentifierValue",
                ).text = identifier.licensedocumentationidentifiervalue
                etree.SubElement(
                    licenseDocumentIdentifier, ns.premisBNS + "licenseDocumentationRole"
                ).text = identifier.licensedocumentationidentifierrole

            etree.SubElement(
                licenseInformation, ns.premisBNS + "licenseTerms"
            ).text = license.licenseterms

            for note in license.rightsstatementlicensenote_set.all():
                etree.SubElement(
                    licenseInformation, ns.premisBNS + "licenseNote"
                ).text = note.licensenote

            _add_start_end_date_complex_type(
                "licenseApplicableDates",
                licenseInformation,
                license.licenseapplicablestartdate,
                license.licenseapplicableenddate,
                license.licenseenddateopen,
            )

    elif statement.rightsbasis.lower() in ["statute"]:
        # 4.1.5 statuteInformation (O, R)
        getstatuteInformation(statement, rightsStatement)

    elif statement.rightsbasis.lower() in ["donor", "policy", "other"]:
        otherRightsInformation = etree.SubElement(
            rightsStatement, ns.premisBNS + "otherRightsInformation"
        )
        for info in statement.rightsstatementotherrightsinformation_set.all():
            # otherRightsDocumentationIdentifier
            for (
                identifier
            ) in info.rightsstatementotherrightsdocumentationidentifier_set.all():
                otherRightsDocumentationIdentifier = etree.SubElement(
                    otherRightsInformation,
                    ns.premisBNS + "otherRightsDocumentationIdentifier",
                )
                etree.SubElement(
                    otherRightsDocumentationIdentifier,
                    ns.premisBNS + "otherRightsDocumentationIdentifierType",
                ).text = identifier.otherrightsdocumentationidentifiertype
                etree.SubElement(
                    otherRightsDocumentationIdentifier,
                    ns.premisBNS + "otherRightsDocumentationIdentifierValue",
                ).text = identifier.otherrightsdocumentationidentifiervalue
                etree.SubElement(
                    otherRightsDocumentationIdentifier,
                    ns.premisBNS + "otherRightsDocumentationRole",
                ).text = identifier.otherrightsdocumentationidentifierrole

            otherRightsBasis = info.otherrightsbasis

            if (
                not otherRightsBasis or statement.rightsbasis in RIGHTS_BASIS_OTHER
            ):  # not 100%
                otherRightsBasis = statement.rightsbasis
            etree.SubElement(
                otherRightsInformation, ns.premisBNS + "otherRightsBasis"
            ).text = otherRightsBasis

            _add_start_end_date_complex_type(
                "otherRightsApplicableDates",
                otherRightsInformation,
                info.otherrightsapplicablestartdate,
                info.otherrightsapplicableenddate,
                info.otherrightsenddateopen,
            )

            # otherRightsNote Repeatable
            for note in info.rightsstatementotherrightsinformationnote_set.all():
                etree.SubElement(
                    otherRightsInformation, ns.premisBNS + "otherRightsNote"
                ).text = note.otherrightsnote

    # 4.1.6 rightsGranted (O, R)
    getrightsGranted(job, statement, rightsStatement, state)

    # 4.1.7 linkingObjectIdentifier (O, R)
    linkingObjectIdentifier = etree.SubElement(
        rightsStatement, ns.premisBNS + "linkingObjectIdentifier"
    )
    etree.SubElement(
        linkingObjectIdentifier, ns.premisBNS + "linkingObjectIdentifierType"
    ).text = "UUID"
    etree.SubElement(
        linkingObjectIdentifier, ns.premisBNS + "linkingObjectIdentifierValue"
    ).text = fileUUID
    return rightsStatement


def getDocumentationIdentifier(copyright, parent):
    for (
        identifier
    ) in copyright.rightsstatementcopyrightdocumentationidentifier_set.all():
        statuteInformation = etree.SubElement(
            parent, ns.premisBNS + "copyrightDocumentationIdentifier"
        )
        etree.SubElement(
            statuteInformation, ns.premisBNS + "copyrightDocumentationIdentifierType"
        ).text = identifier.copyrightdocumentationidentifiertype
        etree.SubElement(
            statuteInformation, ns.premisBNS + "copyrightDocumentationIdentifierValue"
        ).text = identifier.copyrightdocumentationidentifiervalue
        etree.SubElement(
            statuteInformation, ns.premisBNS + "copyrightDocumentationRole"
        ).text = identifier.copyrightdocumentationidentifierrole


def getstatuteInformation(statement, parent):
    for statute in statement.rightsstatementstatuteinformation_set.all():
        statuteInformation = etree.SubElement(
            parent, ns.premisBNS + "statuteInformation"
        )
        etree.SubElement(
            statuteInformation, ns.premisBNS + "statuteJurisdiction"
        ).text = statute.statutejurisdiction
        etree.SubElement(
            statuteInformation, ns.premisBNS + "statuteCitation"
        ).text = statute.statutecitation
        etree.SubElement(
            statuteInformation, ns.premisBNS + "statuteInformationDeterminationDate"
        ).text = formatDate(statute.statutedeterminationdate)

        # statuteNote Repeatable
        for note in statute.rightsstatementstatuteinformationnote_set.all():
            etree.SubElement(
                statuteInformation, ns.premisBNS + "statuteNote"
            ).text = note.statutenote

        for (
            identifier
        ) in statute.rightsstatementstatutedocumentationidentifier_set.all():
            statuteDocumentationIdentifier = etree.SubElement(
                statuteInformation, ns.premisBNS + "statuteDocumentationIdentifier"
            )
            etree.SubElement(
                statuteDocumentationIdentifier,
                ns.premisBNS + "statuteDocumentationIdentifierType",
            ).text = identifier.statutedocumentationidentifiertype
            etree.SubElement(
                statuteDocumentationIdentifier,
                ns.premisBNS + "statuteDocumentationIdentifierValue",
            ).text = identifier.statutedocumentationidentifiervalue
            etree.SubElement(
                statuteDocumentationIdentifier,
                ns.premisBNS + "statuteDocumentationRole",
            ).text = identifier.statutedocumentationidentifierrole

        _add_start_end_date_complex_type(
            "statuteApplicableDates",
            statuteInformation,
            statute.statuteapplicablestartdate,
            statute.statuteapplicableenddate,
            statute.statuteenddateopen,
        )


def getrightsGranted(job, statement, parent, state):
    for granted in statement.rightsstatementrightsgranted_set.all():
        rightsGranted = etree.SubElement(parent, ns.premisBNS + "rightsGranted")
        etree.SubElement(rightsGranted, ns.premisBNS + "act").text = granted.act

        restriction = "Undefined"
        for restriction in granted.restrictions.all():
            restriction = restriction.restriction
            if not restriction.lower() in ["disallow", "conditional", "allow"]:
                job.pyprint(
                    "The value of element restriction must be: 'Allow', 'Disallow', or 'Conditional':",
                    restriction,
                    file=sys.stderr,
                )
                state.error_accumulator.error_count += 1
            etree.SubElement(
                rightsGranted, ns.premisBNS + "restriction"
            ).text = restriction

        if granted.startdate or granted.enddate or granted.enddateopen:
            restriction = restriction.lower()
            if restriction in ("allow",):
                term = "termOfGrant"
            elif restriction in ("disallow", "conditional"):
                term = "termOfRestriction"
            else:
                job.pyprint(
                    "The value of element restriction must be: 'Allow', "
                    "'Disallow', or 'Conditional'",
                    file=sys.stderr,
                )
                state.error_accumulator.error_count += 1
                continue
            _add_start_end_date_complex_type(
                term,
                rightsGranted,
                granted.startdate,
                granted.enddate,
                granted.enddateopen,
            )

        # 4.1.6.4 rightsGrantedNote (O, R)
        for note in granted.notes.all():
            etree.SubElement(
                rightsGranted, ns.premisBNS + "rightsGrantedNote"
            ).text = note.rightsgrantednote
