#!/usr/bin/python -OO
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

#/src/dashboard/src/main/models.py

import sys
import uuid
import lxml.etree as etree

# dashboard
from main.models import RightsStatement

import archivematicaXMLNamesSpace as ns
# archivematicaCommon
from countryCodes import getCodeForCountry
from sharedVariablesAcrossModules import sharedVariablesAcrossModules


def formatDate(date):
    """hack fix for 0.8, easy dashboard insertion ISO 8061 -> edtfSimpleType"""
    if date:
        date = date.replace("/", "-")
    return date


def archivematicaGetRights(metadataAppliesToList, fileUUID):
    """[(fileUUID, fileUUIDTYPE), (sipUUID, sipUUIDTYPE), (transferUUID, transferUUIDType)]"""
    ret = []
    rightsBasisActuallyOther = ["Policy", "Donor"]
    for metadataAppliesToidentifier, metadataAppliesToType in metadataAppliesToList:
        statements = RightsStatement.objects.filter(
            metadataappliestoidentifier=metadataAppliesToidentifier,
            metadataappliestotype_id=metadataAppliesToType
        )
        for statement in statements:
            rightsStatement = etree.Element(ns.premisBNS + "rightsStatement", nsmap={'premis': ns.premisNS})
            rightsStatement.set(ns.xsiBNS+"schemaLocation", ns.premisNS + " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd")
            # rightsStatement.set("version", "2.1") # cvc-complex-type.3.2.2: Attribute 'version' is not allowed to appear in element 'rightsStatement'.

            rightsStatementIdentifier = etree.SubElement(rightsStatement, ns.premisBNS + "rightsStatementIdentifier")
            if statement.rightsstatementidentifiervalue:
                etree.SubElement(rightsStatementIdentifier, ns.premisBNS + "rightsStatementIdentifierType").text = statement.rightsstatementidentifiertype
                etree.SubElement(rightsStatementIdentifier, ns.premisBNS + "rightsStatementIdentifierValue").text = statement.rightsstatementidentifiervalue
            else:
                etree.SubElement(rightsStatementIdentifier, ns.premisBNS + "rightsStatementIdentifierType").text = "UUID"
                etree.SubElement(rightsStatementIdentifier, ns.premisBNS + "rightsStatementIdentifierValue").text = uuid.uuid4().__str__()
            if statement.rightsbasis in rightsBasisActuallyOther:
                etree.SubElement(rightsStatement, ns.premisBNS + "rightsBasis").text = "Other"
            else:
                etree.SubElement(rightsStatement, ns.premisBNS + "rightsBasis").text = statement.rightsbasis

            # Copyright information
            if statement.rightsbasis.lower() in ["copyright"]:
                for copyright in statement.rightsstatementcopyright_set.all():
                    copyrightInformation = etree.SubElement(rightsStatement, ns.premisBNS + "copyrightInformation")
                    etree.SubElement(copyrightInformation, ns.premisBNS + "copyrightStatus").text = copyright.copyrightstatus
                    copyrightJurisdiction = copyright.copyrightjurisdiction
                    copyrightJurisdictionCode = getCodeForCountry(copyrightJurisdiction.__str__().upper())
                    if copyrightJurisdictionCode != None:
                        copyrightJurisdiction = copyrightJurisdictionCode 
                    etree.SubElement(copyrightInformation, ns.premisBNS + "copyrightJurisdiction").text = copyrightJurisdiction 
                    etree.SubElement(copyrightInformation, ns.premisBNS + "copyrightStatusDeterminationDate").text = formatDate(copyright.copyrightstatusdeterminationdate)
                    # copyrightNote Repeatable
                    for note in copyright.rightsstatementcopyrightnote_set.all():
                        etree.SubElement(copyrightInformation, ns.premisBNS + "copyrightNote").text = note.copyrightnote
                        
                    # RightsStatementCopyrightDocumentationIdentifier
                    getDocumentationIdentifier(copyright.rightsstatement, copyrightInformation)

                    copyrightApplicableDates = etree.SubElement(copyrightInformation, ns.premisBNS + "copyrightApplicableDates")
                    if copyright.copyrightapplicablestartdate:
                        etree.SubElement(copyrightApplicableDates, ns.premisBNS + "startDate").text = formatDate(copyright.copyrightapplicablestartdate)
                    if copyright.copyrightenddateopen:
                        etree.SubElement(copyrightApplicableDates, ns.premisBNS + "endDate").text = "OPEN"
                    elif copyright.copyrightapplicableenddate:
                        etree.SubElement(copyrightApplicableDates, ns.premisBNS + "endDate").text = formatDate(copyright.copyrightapplicableenddate)

            elif statement.rightsbasis.lower() in ["license"]:
                for license in statement.rightsstatementlicense_set.all():
                    identifier = license.rightsstatementlicensedocumentationidentifier_set.get()

                    licenseInformation = etree.SubElement(rightsStatement, ns.premisBNS + "licenseInformation")
                    
                    licenseDocumentIdentifier = etree.SubElement(licenseInformation, ns.premisBNS + "licenseDocumentationIdentifier")
                    etree.SubElement(licenseDocumentIdentifier, ns.premisBNS + "licenseDocumentationIdentifierType").text = identifier.licensedocumentationidentifiertype
                    etree.SubElement(licenseDocumentIdentifier, ns.premisBNS + "licenseDocumentationIdentifierValue").text = identifier.licensedocumentationidentifiervalue
                    etree.SubElement(licenseDocumentIdentifier, ns.premisBNS + "licenseDocumentationRole").text = identifier.licensedocumentationidentifierrole
                    
                    etree.SubElement(licenseInformation, ns.premisBNS + "licenseTerms").text = license.licenseterms

                    for note in license.rightsstatementlicensenote_set.all():
                        etree.SubElement(licenseInformation, ns.premisBNS + "licenseNote").text = note.licensenote
                        
                    licenseApplicableDates = etree.SubElement(licenseInformation, ns.premisBNS + "licenseApplicableDates")
                    if license.licenseapplicablestartdate:
                        etree.SubElement(licenseApplicableDates, ns.premisBNS + "startDate").text = formatDate(license.licenseapplicablestartdate)
                    if license.licenseenddateopen:
                        etree.SubElement(licenseApplicableDates, ns.premisBNS + "endDate").text = "OPEN"
                    elif license.licenseapplicableenddate:
                        etree.SubElement(licenseApplicableDates, ns.premisBNS + "endDate").text = formatDate(license.licenseapplicableenddate)

            elif statement.rightsbasis.lower() in ["statute"]:
                # 4.1.5 statuteInformation (O, R)
                getstatuteInformation(statement, rightsStatement)

            elif statement.rightsbasis.lower() in ["donor", "policy", "other"]:
                otherRightsInformation = etree.SubElement(rightsStatement, ns.premisBNS + "otherRightsInformation")
                for info in statement.rightsstatementotherrightsinformation_set.all():
                    # otherRightsDocumentationIdentifier
                    for identifier in info.rightsstatementotherrightsdocumentationidentifier_set.all():
                        otherRightsDocumentationIdentifier = etree.SubElement(otherRightsInformation, ns.premisBNS + "otherRightsDocumentationIdentifier")
                        etree.SubElement(otherRightsDocumentationIdentifier, ns.premisBNS + "otherRightsDocumentationIdentifierType").text = identifier.otherrightsdocumentationidentifiertype
                        etree.SubElement(otherRightsDocumentationIdentifier, ns.premisBNS + "otherRightsDocumentationIdentifierValue").text = identifier.otherrightsdocumentationidentifiervalue
                        etree.SubElement(otherRightsDocumentationIdentifier, ns.premisBNS + "otherRightsDocumentationRole").text = identifier.otherrightsdocumentationidentifierrole

                    otherRightsBasis = info.otherrightsbasis

                    if not otherRightsBasis or statement.rightsbasis in rightsBasisActuallyOther: # not 100%
                        otherRightsBasis = statement.rightsbasis
                    etree.SubElement(otherRightsInformation, ns.premisBNS + "otherRightsBasis").text = otherRightsBasis

                    if info.otherrightsapplicablestartdate or info.otherrightsapplicableenddate:
                        otherRightsApplicableDates = etree.SubElement(otherRightsInformation, ns.premisBNS + "otherRightsApplicableDates")
                        if info.otherrightsapplicablestartdate:
                            etree.SubElement(otherRightsApplicableDates, ns.premisBNS + "startDate").text = formatDate(info.otherrightsapplicablestartdate)
                        if info.otherrightsapplicableenddateopen:
                            etree.SubElement(otherRightsApplicableDates, ns.premisBNS + "endDate").text = "OPEN"
                        elif info.otherrightsapplicableenddate:
                            etree.SubElement(otherRightsApplicableDates, ns.premisBNS + "endDate").text = formatDate(info.otherrightsapplicableenddate)

                    # otherRightsNote Repeatable
                    for note in info.rightsstatementotherrightsinformationnote_set.all():
                        etree.SubElement(otherRightsInformation, ns.premisBNS + "otherRightsNote").text = note.otherrightsnote

            # 4.1.6 rightsGranted (O, R)
            getrightsGranted(statement, rightsStatement)

            # 4.1.7 linkingObjectIdentifier (O, R)
            linkingObjectIdentifier = etree.SubElement(rightsStatement, ns.premisBNS + "linkingObjectIdentifier")
            etree.SubElement(linkingObjectIdentifier, ns.premisBNS + "linkingObjectIdentifierType").text = "UUID"
            etree.SubElement(linkingObjectIdentifier, ns.premisBNS + "linkingObjectIdentifierValue").text = fileUUID
    return ret

def getDocumentationIdentifier(identifier, parent):
    statuteInformation = etree.SubElement(parent, ns.premisBNS + "copyrightDocumentationIdentifier")
    etree.SubElement(statuteInformation, ns.premisBNS + "copyrightDocumentationIdentifierType").text = identifier.copyrightdocumentationidentifiertype
    etree.SubElement(statuteInformation, ns.premisBNS + "copyrightDocumentationIdentifierValue").text = identifier.copyrightdocumentationidentifiervalue
    etree.SubElement(statuteInformation, ns.premisBNS + "copyrightDocumentationRole").text = identifier.copyrightdocumentationidentifierrole


def getstatuteInformation(statement, parent):
    for statute in statement.rightsstatementstatuteinformation_set.all():
        statuteInformation = etree.SubElement(parent, ns.premisBNS + "statuteInformation")
        etree.SubElement(statuteInformation, ns.premisBNS + "statuteJurisdiction").text = statute.statutejurisdiction
        etree.SubElement(statuteInformation, ns.premisBNS + "statuteCitation").text = statute.statutecitation
        etree.SubElement(statuteInformation, ns.premisBNS + "statuteInformationDeterminationDate").text = formatDate(statute.statutedeterminationdate)

        # statuteNote Repeatable
        for note in statute.rightsstatementstatuteinformationnote_set.all():
            etree.SubElement(statuteInformation, ns.premisBNS + "statuteNote").text = note.statutenote

        for identifier in statute.rightsstatementstatutedocumentationidentifier_set.all():
            statuteDocumentationIdentifier = etree.SubElement(statuteInformation, ns.premisBNS + "statuteDocumentationIdentifier")
            etree.SubElement(statuteDocumentationIdentifier, ns.premisBNS + "statuteDocumentationIdentifierType").text = identifier.statutedocumentationidentifiertype
            etree.SubElement(statuteDocumentationIdentifier, ns.premisBNS + "statuteDocumentationIdentifierValue").text = identifier.statutedocumentationidentifiervalue
            etree.SubElement(statuteDocumentationIdentifier, ns.premisBNS + "statuteDocumentationRole").text = identifier.statutedocumentationidentifierrole

        statuteapplicablestartdate = statute.statuteapplicablestartdate
        statuteapplicableenddate = statute.statuteapplicableenddate
        statuteApplicableEndDateOpen = statute.statuteenddateopen
        if statuteapplicablestartdate or statuteapplicableenddate or statuteApplicableEndDateOpen:
             statuteApplicableDates = etree.SubElement(statuteInformation, ns.premisBNS + "statuteApplicableDates")
             if statuteapplicablestartdate: 
                etree.SubElement(statuteApplicableDates, ns.premisBNS + "startDate").text = formatDate(statuteapplicablestartdate)
             if statuteApplicableEndDateOpen:
                 etree.SubElement(statuteApplicableDates, ns.premisBNS + "endDate").text = "OPEN"
             elif statuteapplicableenddate:
                 etree.SubElement(statuteApplicableDates, ns.premisBNS + "endDate").text = formatDate(statuteapplicableenddate)


def getrightsGranted(statement, parent):
    for granted in statement.rightsstatementrightsgranted_set.all():
        rightsGranted = etree.SubElement(parent, ns.premisBNS + "rightsGranted")
        etree.SubElement(rightsGranted, ns.premisBNS + "act").text = granted.act
        
        restriction = "Undefined"
        for restriction in granted.rightsstatementrightsgrantedrestriction_set.all():
            restriction = restriction.restriction
            if not restriction.lower() in ["disallow", "conditional", "allow"]:
                print >>sys.stderr, "The value of element restriction must be: 'Allow', 'Disallow', or 'Conditional':", restriction
                sharedVariablesAcrossModules.globalErrorCount +=1
            etree.SubElement(rightsGranted, ns.premisBNS + "restriction").text = restriction
        
        if granted.startdate or granted.enddate or granted.enddateopen:
            if restriction.lower() in ["allow"]:
                termOfGrant = etree.SubElement(rightsGranted, ns.premisBNS + "termOfGrant")
            elif restriction.lower() in ["disallow", "conditional"]:
                termOfGrant = etree.SubElement(rightsGranted, ns.premisBNS + "termOfRestriction")
            else:
                print >>sys.stderr, "The value of element restriction must be: 'Allow', 'Disallow', or 'Conditional'"
                sharedVariablesAcrossModules.globalErrorCount +=1
                continue

            if granted.startdate:
                etree.SubElement(termOfGrant, ns.premisBNS + "startDate").text = formatDate(granted.startdate)
            if granted.enddateopen:
                etree.SubElement(termOfGrant, ns.premisBNS + "endDate").text = "OPEN"
            elif granted.enddate:
                etree.SubElement(termOfGrant, ns.premisBNS + "endDate").text = formatDate(granted.enddate)

        # 4.1.6.4 rightsGrantedNote (O, R)
        for note in granted.rightsstatementrightsgrantednote_set.all():
            etree.SubElement(rightsGranted, ns.premisBNS + "rightsGrantedNote").text = note.rightsgrantednote
