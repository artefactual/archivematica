# -*- coding: utf8
from lxml import etree
import os
import sys

from django.test import TestCase

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
import parse_mets_to_db

from job import Job

import fpr
from main import models


class TestParseDublinCore(TestCase):
    """ Test parsing SIP-level DublinCore from a METS file into the DB. """

    fixture_files = ["metadata_applies_to_type.json", "dublincore.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def test_none_found(self):
        """ It should parse no DC if none is found. """
        sip_uuid = "d481580e-53b9-4a52-96db-baa969e78adc"
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_no_metadata.xml"))
        dc = parse_mets_to_db.parse_dc(Job("stub", "stub", []), sip_uuid, root)
        assert dc is None
        assert (
            models.DublinCore.objects.filter(
                metadataappliestoidentifier=sip_uuid
            ).exists()
            is False
        )

    def test_no_sip_dc(self):
        """ It should ignore file-level DC. """
        sip_uuid = "f35d2530-45eb-4eb1-aa09-fb30661e7dcd"
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_only_file_dc.xml"))
        dc = parse_mets_to_db.parse_dc(Job("stub", "stub", []), sip_uuid, root)
        assert dc is None
        assert (
            models.DublinCore.objects.filter(
                metadataappliestoidentifier=sip_uuid
            ).exists()
            is False
        )

    def test_only_original(self):
        """ It should parse a SIP-level DC if found. """
        sip_uuid = "eacbf65f-2528-4be0-8cb3-532f45fcdff8"
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_sip_dc.xml"))
        dc = parse_mets_to_db.parse_dc(Job("stub", "stub", []), sip_uuid, root)
        assert dc
        assert models.DublinCore.objects.filter(
            metadataappliestoidentifier=sip_uuid
        ).exists()
        assert dc.title == "Yamani Weapons"
        assert dc.creator == "Keladry of Mindelan"
        assert dc.subject == "Glaives"
        assert dc.description == "Glaives are cool"
        assert dc.publisher == "Tortall Press"
        assert dc.contributor == "Yuki"
        assert dc.date == "2014"
        assert dc.type == "Archival Information Package"
        assert dc.format == "parchement"
        assert dc.identifier == "42/1"
        assert dc.source == "Numair's library"
        assert dc.relation == "None"
        assert dc.language == "en"
        assert dc.rights == "Public Domain"
        assert dc.is_part_of == "AIC#43"

    def test_get_sip_dc_ignore_file_dc(self):
        """ It should parse a SIP-level DC even if file-level DC is also present. """
        sip_uuid = "55972e97-8d35-4b07-abaa-ae260c32d261"
        root = etree.parse(
            os.path.join(THIS_DIR, "fixtures", "mets_sip_and_file_dc.xml")
        )
        dc = parse_mets_to_db.parse_dc(Job("stub", "stub", []), sip_uuid, root)
        assert dc
        assert models.DublinCore.objects.filter(
            metadataappliestoidentifier=sip_uuid
        ).exists()
        assert dc.title == "Yamani Weapons"
        assert dc.creator == "Keladry of Mindelan"
        assert dc.subject == "Glaives"
        assert dc.description == "Glaives are cool"
        assert dc.publisher == "Tortall Press"
        assert dc.contributor == "Yuki"
        assert dc.date == "2014"
        assert dc.type == "Archival Information Package"
        assert dc.format == "parchement"
        assert dc.identifier == "42/1"
        assert dc.source == "Numair's library"
        assert dc.relation == "None"
        assert dc.language == "en"
        assert dc.rights == "Public Domain"
        assert dc.is_part_of == "AIC#43"

    def test_multiple_sip_dc(self):
        """ It should parse the most recent SIP DC if multiple exist. """
        sip_uuid = "eacbf65f-2528-4be0-8cb3-532f45fcdff8"
        root = etree.parse(
            os.path.join(THIS_DIR, "fixtures", "mets_multiple_sip_dc.xml")
        )
        dc = parse_mets_to_db.parse_dc(Job("stub", "stub", []), sip_uuid, root)
        assert dc
        assert models.DublinCore.objects.filter(
            metadataappliestoidentifier=sip_uuid
        ).exists()
        assert dc.title == "Yamani Weapons"
        assert dc.creator == "Keladry of Mindelan"
        assert dc.subject == "Glaives"
        assert dc.description == "Glaives are awesome"
        assert dc.publisher == "Tortall Press"
        assert dc.contributor == "Yuki"
        assert dc.date == "2014"
        assert dc.type == "Archival Information Package"
        assert dc.format == "palimpsest"
        assert dc.identifier == "42/1"
        assert dc.source == ""
        assert dc.relation == "Everyone!"
        assert dc.language == "en"
        assert dc.rights == "Public Domain"
        assert dc.is_part_of == "AIC#43"


class TestParsePremisRights(TestCase):
    """ Test parsing PREMIS:RIGHTS from a METS file into the DB. """

    fixture_files = ["metadata_applies_to_type.json", "dublincore.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def test_none_found(self):
        """ It should parse no rights if none found. """
        sip_uuid = "d481580e-53b9-4a52-96db-baa969e78adc"
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_no_metadata.xml"))
        rights = parse_mets_to_db.parse_rights(Job("stub", "stub", []), sip_uuid, root)
        assert rights == []
        assert (
            models.RightsStatement.objects.filter(
                metadataappliestoidentifier=sip_uuid
            ).exists()
            is False
        )

    def test_parse_copyright(self):
        """
        It should parse copyright rights.
        It should parse multiple rightsGranted.
        """
        sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_all_rights.xml"))
        rights_list = parse_mets_to_db.parse_rights(
            Job("stub", "stub", []), sip_uuid, root
        )
        assert rights_list
        rights = models.RightsStatement.objects.get(
            metadataappliestoidentifier=sip_uuid, rightsbasis="Copyright"
        )
        assert rights.rightsstatementidentifiertype == ""
        assert rights.rightsstatementidentifiervalue == ""
        assert rights.rightsholder == 0
        assert rights.rightsbasis == "Copyright"
        assert rights.status == "REINGEST"
        cr = models.RightsStatementCopyright.objects.get(rightsstatement=rights)
        assert cr.copyrightstatus == "Under copyright"
        assert cr.copyrightjurisdiction == "CA"
        assert cr.copyrightstatusdeterminationdate == "2015"
        assert cr.copyrightapplicablestartdate == "1990"
        assert cr.copyrightapplicableenddate is None
        assert cr.copyrightenddateopen is True
        di = models.RightsStatementCopyrightDocumentationIdentifier.objects.get(
            rightscopyright=cr
        )
        assert di.copyrightdocumentationidentifiertype == ""
        assert di.copyrightdocumentationidentifiervalue == ""
        assert di.copyrightdocumentationidentifierrole == ""
        note = models.RightsStatementCopyrightNote.objects.get(rightscopyright=cr)
        assert note.copyrightnote == "Copyright expires 2010"
        rg = models.RightsStatementRightsGranted.objects.filter(rightsstatement=rights)
        assert len(rg) == 2
        assert rg[0].act == "Disseminate"
        assert rg[0].startdate == "2000"
        assert rg[0].enddate is None
        assert rg[0].enddateopen is True
        rgnote = models.RightsStatementRightsGrantedNote.objects.get(
            rightsgranted=rg[0]
        )
        assert rgnote.rightsgrantednote == "Attribution required"
        rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
            rightsgranted=rg[0]
        )
        assert rgrestriction.restriction == "Allow"
        assert rg[1].act == "Access"
        assert rg[1].startdate == "1999"
        assert rg[1].enddate is None
        assert rg[1].enddateopen is True
        rgnote = models.RightsStatementRightsGrantedNote.objects.get(
            rightsgranted=rg[1]
        )
        assert rgnote.rightsgrantednote == "Access one year before dissemination"
        rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
            rightsgranted=rg[1]
        )
        assert rgrestriction.restriction == "Allow"

    def test_parse_license(self):
        """ It should parse license rights. """
        sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_all_rights.xml"))
        rights_list = parse_mets_to_db.parse_rights(
            Job("stub", "stub", []), sip_uuid, root
        )
        assert rights_list
        rights = models.RightsStatement.objects.get(
            metadataappliestoidentifier=sip_uuid, rightsbasis="License"
        )
        assert rights.rightsstatementidentifiertype == ""
        assert rights.rightsstatementidentifiervalue == ""
        assert rights.rightsholder == 0
        assert rights.rightsbasis == "License"
        assert rights.status == "REINGEST"
        li = models.RightsStatementLicense.objects.get(rightsstatement=rights)
        assert li.licenseterms == "CC-BY-SA"
        assert li.licenseapplicablestartdate == "2015"
        assert li.licenseapplicableenddate is None
        assert li.licenseenddateopen is True
        di = models.RightsStatementLicenseDocumentationIdentifier.objects.get(
            rightsstatementlicense=li
        )
        assert di.licensedocumentationidentifiertype == ""
        assert di.licensedocumentationidentifiervalue == ""
        assert di.licensedocumentationidentifierrole == ""
        note = models.RightsStatementLicenseNote.objects.get(rightsstatementlicense=li)
        assert note.licensenote == ""
        rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
        assert rg.act == "Disseminate"
        assert rg.startdate == "2015"
        assert rg.enddate is None
        assert rg.enddateopen is True
        rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
        assert rgnote.rightsgrantednote == "Attribution required"
        rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
            rightsgranted=rg
        )
        assert rgrestriction.restriction == "Allow"

    def test_parse_statute(self):
        """ It should parse statute rights. """
        sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_all_rights.xml"))
        rights_list = parse_mets_to_db.parse_rights(
            Job("stub", "stub", []), sip_uuid, root
        )
        assert rights_list
        rights = models.RightsStatement.objects.get(
            metadataappliestoidentifier=sip_uuid, rightsbasis="Statute"
        )
        assert rights.rightsstatementidentifiertype == ""
        assert rights.rightsstatementidentifiervalue == ""
        assert rights.rightsholder == 0
        assert rights.rightsbasis == "Statute"
        assert rights.status == "REINGEST"
        st = models.RightsStatementStatuteInformation.objects.get(
            rightsstatement=rights
        )
        assert st.statutejurisdiction == "BC, Canada"
        assert st.statutecitation == "Freedom of Information Act"
        assert st.statutedeterminationdate == "2011"
        assert st.statuteapplicablestartdate == "1994"
        assert st.statuteapplicableenddate == "2094"
        assert st.statuteenddateopen is False
        di = models.RightsStatementStatuteDocumentationIdentifier.objects.get(
            rightsstatementstatute=st
        )
        assert di.statutedocumentationidentifiertype == ""
        assert di.statutedocumentationidentifiervalue == ""
        assert di.statutedocumentationidentifierrole == ""
        note = models.RightsStatementStatuteInformationNote.objects.get(
            rightsstatementstatute=st
        )
        assert note.statutenote == "SIN & health numbers"
        rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
        assert rg.act == "Disseminate"
        assert rg.startdate == "1994"
        assert rg.enddate == "2094"
        assert rg.enddateopen is False
        rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
        assert rgnote.rightsgrantednote == ""
        rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
            rightsgranted=rg
        )
        assert rgrestriction.restriction == "Disallow"

    def test_parse_policy(self):
        """ It should parse policy rights. """
        pass
        sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_all_rights.xml"))
        rights_list = parse_mets_to_db.parse_rights(
            Job("stub", "stub", []), sip_uuid, root
        )
        assert rights_list
        rights = models.RightsStatement.objects.get(
            metadataappliestoidentifier=sip_uuid, rightsbasis="Policy"
        )
        assert rights.rightsstatementidentifiertype == ""
        assert rights.rightsstatementidentifiervalue == ""
        assert rights.rightsholder == 0
        assert rights.rightsbasis == "Policy"
        assert rights.status == "REINGEST"
        other = models.RightsStatementOtherRightsInformation.objects.get(
            rightsstatement=rights
        )
        assert other.otherrightsbasis == "Policy"
        assert other.otherrightsapplicablestartdate == "1989"
        assert other.otherrightsapplicableenddate is None
        assert other.otherrightsenddateopen is True
        di = models.RightsStatementOtherRightsDocumentationIdentifier.objects.get(
            rightsstatementotherrights=other
        )
        assert di.otherrightsdocumentationidentifiertype == ""
        assert di.otherrightsdocumentationidentifiervalue == ""
        assert di.otherrightsdocumentationidentifierrole == ""
        note = models.RightsStatementOtherRightsInformationNote.objects.get(
            rightsstatementotherrights=other
        )
        assert note.otherrightsnote == "Pubic relations office only"
        rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
        assert rg.act == "Disseminate"
        assert rg.startdate == "1989-01-01"
        assert rg.enddate is None
        assert rg.enddateopen is True
        rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
        assert rgnote.rightsgrantednote == ""
        rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
            rightsgranted=rg
        )
        assert rgrestriction.restriction == "Conditional"

    def test_parse_donor(self):
        """ It should parse donor rights. """
        pass
        sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_all_rights.xml"))
        rights_list = parse_mets_to_db.parse_rights(
            Job("stub", "stub", []), sip_uuid, root
        )
        assert rights_list
        rights = models.RightsStatement.objects.get(
            metadataappliestoidentifier=sip_uuid, rightsbasis="Donor"
        )
        assert rights.rightsstatementidentifiertype == ""
        assert rights.rightsstatementidentifiervalue == ""
        assert rights.rightsholder == 0
        assert rights.rightsbasis == "Donor"
        assert rights.status == "REINGEST"
        other = models.RightsStatementOtherRightsInformation.objects.get(
            rightsstatement=rights
        )
        assert other.otherrightsbasis == "Donor"
        assert other.otherrightsapplicablestartdate == "2000-01-01"
        assert other.otherrightsapplicableenddate == "2020-01-01"
        assert other.otherrightsenddateopen is False
        di = models.RightsStatementOtherRightsDocumentationIdentifier.objects.get(
            rightsstatementotherrights=other
        )
        assert di.otherrightsdocumentationidentifiertype == "DID"
        assert di.otherrightsdocumentationidentifiervalue == "1"
        assert di.otherrightsdocumentationidentifierrole == "-"
        note = models.RightsStatementOtherRightsInformationNote.objects.get(
            rightsstatementotherrights=other
        )
        assert note.otherrightsnote == "Contact in 2010 for earlier"
        rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
        assert rg.act == "Publish"
        assert rg.startdate == "2000-01-01"
        assert rg.enddate == "2020-01-01"
        assert rg.enddateopen is False
        rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
        assert rgnote.rightsgrantednote == ""
        rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
            rightsgranted=rg
        )
        assert rgrestriction.restriction == "Conditional"

    def test_parse_multiple_rights(self):
        """ It should only parse the most recent rights. """
        sip_uuid = "50d65db1-86cd-4579-80af-8d9c0dbd7fca"
        root = etree.parse(
            os.path.join(THIS_DIR, "fixtures", "mets_updated_rights.xml")
        )
        rights_list = parse_mets_to_db.parse_rights(
            Job("stub", "stub", []), sip_uuid, root
        )
        assert rights_list
        rights = models.RightsStatement.objects.get(
            metadataappliestoidentifier=sip_uuid, rightsbasis="Statute"
        )
        assert rights.rightsstatementidentifiertype == ""
        assert rights.rightsstatementidentifiervalue == ""
        assert rights.rightsholder == 0
        assert rights.rightsbasis == "Statute"
        assert rights.status == "REINGEST"
        st = models.RightsStatementStatuteInformation.objects.get(
            rightsstatement=rights
        )
        assert st.statutejurisdiction == "British Columbia, Canada"
        assert (
            st.statutecitation
            == "Freedom of Information Act and Protection of Privacy Act"
        )
        assert st.statutedeterminationdate == "2015"
        assert st.statuteapplicablestartdate == "2000"
        assert st.statuteapplicableenddate is None
        assert st.statuteenddateopen is True
        di = models.RightsStatementStatuteDocumentationIdentifier.objects.get(
            rightsstatementstatute=st
        )
        assert di.statutedocumentationidentifiertype == "Doc"
        assert di.statutedocumentationidentifiervalue == "1"
        assert di.statutedocumentationidentifierrole == "-"
        note = models.RightsStatementStatuteInformationNote.objects.get(
            rightsstatementstatute=st
        )
        assert note.statutenote == "SIN and health numbers"
        rg = models.RightsStatementRightsGranted.objects.get(rightsstatement=rights)
        assert rg.act == "Disseminate"
        assert rg.startdate == "2000"
        assert rg.enddate is None
        assert rg.enddateopen is True
        rgnote = models.RightsStatementRightsGrantedNote.objects.get(rightsgranted=rg)
        assert rgnote.rightsgrantednote == ""
        rgrestriction = models.RightsStatementRightsGrantedRestriction.objects.get(
            rightsgranted=rg
        )
        assert rgrestriction.restriction == "Disallow"


class TestParseFiles(TestCase):
    """ Test parsing file information from a METS file to the DB. """

    fixture_files = ["formats.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def setUp(self):
        self.ORIG_INFO = {
            "uuid": "ae8d4290-fe52-4954-b72a-0f591bee2e2f",
            "original_path": "%SIPDirectory%objects/evelyn's photo.jpg",
            "current_path": "%SIPDirectory%objects/evelyn_s_photo.jpg",
            "use": "original",
            "checksum": "d2bed92b73c7090bb30a0b30016882e7069c437488e1513e9deaacbe29d38d92",
            "checksumtype": "sha256",
            "size": "158131",
            "format_version": fpr.models.FormatVersion.objects.get(
                uuid="01fac958-274d-41ef-978f-d9cf711b3c4a"
            ),
            "derivation": "8140ebe5-295c-490b-a34a-83955b7c844e",
            "derivation_event": "0ce13092-911f-4a89-b9e1-0e61921a03d4",
        }
        self.PRES_INFO = {
            "uuid": "8140ebe5-295c-490b-a34a-83955b7c844e",
            "original_path": "%SIPDirectory%objects/evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif",
            "current_path": "%SIPDirectory%objects/evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif",
            "use": "preservation",
            "checksum": "d82448f154b9185bc777ecb0a3602760eb76ba85dd3098f073b2c91a03f571e9",
            "checksumtype": "sha256",
            "size": "1446772",
            "format_version": None,
            "derivation": None,
            "derivation_event": None,
        }
        self.METS_INFO = {
            "uuid": "590bd882-7521-498c-8f89-0958218f779d",
            "original_path": "%SIPDirectory%objects/submissionDocumentation/transfer-no-metadata-46260807-ece1-4a0e-b70a-9814c701146b/METS.xml",
            "current_path": "%SIPDirectory%objects/submissionDocumentation/transfer-no-metadata-46260807-ece1-4a0e-b70a-9814c701146b/METS.xml",
            "use": "submissionDocumentation",
            "checksum": "d41d8cd98f00b204e9800998ecf8427e",
            "checksumtype": "md5",
            "size": "12222",
            "format_version": fpr.models.FormatVersion.objects.get(
                uuid="d60e5243-692e-4af7-90cd-40c53cb8dc7d"
            ),
            "derivation": None,
            "derivation_event": None,
        }
        self.SIP_UUID = "8a0cac37-e446-4fa7-9e96-062bf07ccd04"
        models.SIP.objects.create(uuid=self.SIP_UUID, sip_type="AIP-REIN")

    def test_parse_file_info(self):
        """
        It should parse file info into a dict.
        It should attach derivation information to the original file.
        """
        root = etree.parse(os.path.join(THIS_DIR, "fixtures", "mets_no_metadata.xml"))
        files = parse_mets_to_db.parse_files(Job("stub", "stub", []), root)
        assert len(files) == 3
        orig = files[0]
        assert orig["uuid"] == self.ORIG_INFO["uuid"]
        assert orig["original_path"] == self.ORIG_INFO["original_path"]
        assert orig["current_path"] == self.ORIG_INFO["current_path"]
        assert orig["use"] == self.ORIG_INFO["use"]
        assert orig["checksum"] == self.ORIG_INFO["checksum"]
        assert orig["checksumtype"] == self.ORIG_INFO["checksumtype"]
        assert orig["size"] == self.ORIG_INFO["size"]
        assert orig["format_version"] == self.ORIG_INFO["format_version"]
        assert orig["derivation"] == self.ORIG_INFO["derivation"]
        assert orig["derivation_event"] == self.ORIG_INFO["derivation_event"]
        mets = files[1]
        assert mets["uuid"] == self.METS_INFO["uuid"]
        assert mets["original_path"] == self.METS_INFO["original_path"]
        assert mets["current_path"] == self.METS_INFO["current_path"]
        assert mets["use"] == self.METS_INFO["use"]
        assert mets["checksum"] == self.METS_INFO["checksum"]
        assert mets["checksumtype"] == self.METS_INFO["checksumtype"]
        assert mets["size"] == self.METS_INFO["size"]
        assert mets["format_version"] == self.METS_INFO["format_version"]
        assert mets["derivation"] == self.METS_INFO["derivation"]
        assert mets["derivation_event"] == self.METS_INFO["derivation_event"]
        pres = files[2]
        assert pres["uuid"] == self.PRES_INFO["uuid"]
        assert pres["original_path"] == self.PRES_INFO["original_path"]
        assert pres["current_path"] == self.PRES_INFO["current_path"]
        assert pres["use"] == self.PRES_INFO["use"]
        assert pres["checksum"] == self.PRES_INFO["checksum"]
        assert pres["checksumtype"] == self.PRES_INFO["checksumtype"]
        assert pres["size"] == self.PRES_INFO["size"]
        assert pres["format_version"] == self.PRES_INFO["format_version"]
        assert pres["derivation"] == self.PRES_INFO["derivation"]
        assert pres["derivation_event"] == self.PRES_INFO["derivation_event"]

    def test_parse_file_info_reingest(self):
        """
        It should parse the correct techMD in the amdSec.
        """
        root = etree.parse(
            os.path.join(THIS_DIR, "fixtures", "mets_superseded_techmd.xml")
        )
        files = parse_mets_to_db.parse_files(Job("stub", "stub", []), root)
        assert len(files) == 3
        orig = files[0]
        assert orig["uuid"] == self.ORIG_INFO["uuid"]
        assert orig["original_path"] == self.ORIG_INFO["original_path"]
        assert orig["current_path"] == self.ORIG_INFO["current_path"]
        assert orig["use"] == self.ORIG_INFO["use"]
        assert orig["checksum"] == self.ORIG_INFO["checksum"]
        assert orig["checksumtype"] == self.ORIG_INFO["checksumtype"]
        assert orig["size"] == self.ORIG_INFO["size"]
        assert orig["format_version"] == self.ORIG_INFO["format_version"]
        assert orig["derivation"] == self.ORIG_INFO["derivation"]
        assert orig["derivation_event"] == self.ORIG_INFO["derivation_event"]
        mets = files[1]
        assert mets["uuid"] == self.METS_INFO["uuid"]
        assert mets["original_path"] == self.METS_INFO["original_path"]
        assert mets["current_path"] == self.METS_INFO["current_path"]
        assert mets["use"] == self.METS_INFO["use"]
        assert mets["checksum"] == self.METS_INFO["checksum"]
        assert mets["checksumtype"] == self.METS_INFO["checksumtype"]
        assert mets["size"] == self.METS_INFO["size"]
        assert mets["format_version"] == self.METS_INFO["format_version"]
        assert mets["derivation"] == self.METS_INFO["derivation"]
        assert mets["derivation_event"] == self.METS_INFO["derivation_event"]
        pres = files[2]
        assert pres["uuid"] == self.PRES_INFO["uuid"]
        assert pres["original_path"] == self.PRES_INFO["original_path"]
        assert pres["current_path"] == self.PRES_INFO["current_path"]
        assert pres["use"] == self.PRES_INFO["use"]
        assert pres["checksum"] == self.PRES_INFO["checksum"]
        assert pres["checksumtype"] == self.PRES_INFO["checksumtype"]
        assert pres["size"] == self.PRES_INFO["size"]
        assert pres["format_version"] == self.PRES_INFO["format_version"]
        assert pres["derivation"] == self.PRES_INFO["derivation"]
        assert pres["derivation_event"] == self.PRES_INFO["derivation_event"]

    def test_insert_file_info(self):
        """ It should insert file info into the DB. """
        files = [self.METS_INFO, self.PRES_INFO, self.ORIG_INFO]
        parse_mets_to_db.update_files(self.SIP_UUID, files)
        # Verify original file
        orig = models.File.objects.get(uuid=self.ORIG_INFO["uuid"])
        assert orig.sip_id == self.SIP_UUID
        assert orig.transfer is None
        assert orig.originallocation == self.ORIG_INFO["original_path"]
        assert orig.currentlocation == self.ORIG_INFO["current_path"]
        assert orig.filegrpuse == self.ORIG_INFO["use"]
        assert orig.filegrpuuid == ""
        assert orig.checksum == self.ORIG_INFO["checksum"]
        assert orig.checksumtype == self.ORIG_INFO["checksumtype"]
        assert orig.size == int(self.ORIG_INFO["size"])
        assert models.Event.objects.get(
            file_uuid_id=self.ORIG_INFO["uuid"], event_type="reingestion"
        )
        assert models.FileFormatVersion.objects.get(
            file_uuid_id=self.ORIG_INFO["uuid"],
            format_version=self.ORIG_INFO["format_version"],
        )
        assert models.Derivation.objects.get(
            source_file_id=self.ORIG_INFO["uuid"], derived_file=self.PRES_INFO["uuid"]
        )
        # Verify preservation file
        pres = models.File.objects.get(uuid=self.PRES_INFO["uuid"])
        assert pres.sip_id == self.SIP_UUID
        assert pres.transfer is None
        assert pres.originallocation == self.PRES_INFO["original_path"]
        assert pres.currentlocation == self.PRES_INFO["current_path"]
        assert pres.filegrpuse == self.PRES_INFO["use"]
        assert pres.filegrpuuid == ""
        assert pres.checksum == self.PRES_INFO["checksum"]
        assert pres.checksumtype == self.PRES_INFO["checksumtype"]
        assert pres.size == int(self.PRES_INFO["size"])
        assert models.Event.objects.get(
            file_uuid_id=self.PRES_INFO["uuid"], event_type="reingestion"
        )
        assert (
            models.FileFormatVersion.objects.filter(
                file_uuid_id=self.PRES_INFO["uuid"]
            ).exists()
            is False
        )
        # Verify original file
        mets = models.File.objects.get(uuid=self.METS_INFO["uuid"])
        assert mets.sip_id == self.SIP_UUID
        assert mets.transfer is None
        assert mets.originallocation == self.METS_INFO["original_path"]
        assert mets.currentlocation == self.METS_INFO["current_path"]
        assert mets.filegrpuse == self.METS_INFO["use"]
        assert mets.filegrpuuid == ""
        assert mets.checksum == self.METS_INFO["checksum"]
        assert mets.checksumtype == self.METS_INFO["checksumtype"]
        assert mets.size == int(self.METS_INFO["size"])
        assert models.Event.objects.get(
            file_uuid_id=self.METS_INFO["uuid"], event_type="reingestion"
        )
        assert models.FileFormatVersion.objects.get(
            file_uuid_id=self.METS_INFO["uuid"],
            format_version=self.METS_INFO["format_version"],
        )
        assert (
            models.Derivation.objects.filter(
                source_file_id=self.METS_INFO["uuid"]
            ).exists()
            is False
        )
        assert (
            models.Derivation.objects.filter(
                derived_file=self.METS_INFO["uuid"]
            ).exists()
            is False
        )
