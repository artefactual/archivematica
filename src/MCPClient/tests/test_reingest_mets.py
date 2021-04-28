# -*- coding: utf8
from lxml import etree
import os
import shutil
import sys
import tempfile
import unittest

from django.core.management import call_command
from django.test import TestCase

from main import models

from job import Job
from namespaces import NSMAP, nsmap_for_premis2
from version import get_preservation_system_identifier

import metsrw
from six.moves import range

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(THIS_DIR, "fixtures")
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
import archivematicaCreateMETSReingest

REMOVE_BLANK_PARSER = etree.XMLParser(remove_blank_text=True)


class TestUpdateObject(TestCase):
    """ Test updating the PREMIS:OBJECT in the techMD. (update_object). """

    fixture_files = ["sip-reingest.json", "files.json", "events-reingest.json"]
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    def setUp(self):
        self.sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"

    def load_fixture(self, fixture_paths):
        try:
            call_command("loaddata", *fixture_paths, **{"verbosity": 0})
        except Exception:
            self._fixture_teardown()
            raise

    def test_object_not_updated(self):
        """ It should do nothing if the object has not been updated. """
        # Verify METS state
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 1
        )
        # Run test
        mets = archivematicaCreateMETSReingest.update_object(
            Job("stub", "stub", []), mets
        )
        root = mets.serialize()
        # Verify no change
        assert (
            len(
                root.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 1
        )

    def test_update_checksum_type(self):
        """ It should add a new techMD with the new checksum & checksumtype. """
        # Set checksumtype values
        self.load_fixture([os.path.join(FIXTURES_DIR, "reingest-checksum.json")])
        models.File.objects.filter(uuid="ae8d4290-fe52-4954-b72a-0f591bee2e2f").update(
            checksumtype="md5", checksum="ac63a92ba5a94c337e740d6f189200d0"
        )
        # Verify METS state
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 1
        )
        # Run test
        mets = archivematicaCreateMETSReingest.update_object(
            Job("stub", "stub", []), mets
        )
        root = mets.serialize()
        assert (
            len(
                root.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 2
        )
        # Verify old techMD
        old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
        old_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
        )[0]
        assert old_techmd.attrib["STATUS"] == "superseded"
        namespaces = nsmap_for_premis2()
        assert (
            old_techmd.findtext(
                ".//premis:messageDigestAlgorithm", namespaces=namespaces
            )
            == "sha256"
        )
        assert (
            old_techmd.findtext(".//premis:messageDigest", namespaces=namespaces)
            == "d2bed92b73c7090bb30a0b30016882e7069c437488e1513e9deaacbe29d38d92"
        )
        # Verify new techMD
        new_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
        )[0]
        assert new_techmd.attrib["STATUS"] == "current"
        assert (
            new_techmd.findtext(".//premis:messageDigestAlgorithm", namespaces=NSMAP)
            == "md5"
        )
        assert (
            new_techmd.findtext(".//premis:messageDigest", namespaces=NSMAP)
            == "ac63a92ba5a94c337e740d6f189200d0"
        )
        # Verify rest of new techMD was created
        assert new_techmd.find(".//premis:formatName", namespaces=NSMAP) is not None
        assert (
            new_techmd.find(".//premis:relatedObjectIdentifierType", namespaces=NSMAP)
            is not None
        )
        assert (
            len(
                new_techmd.find(
                    ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
                )
            )
            > 0
        )

    def test_update_file_id(self):
        """ It should add a new techMD with the new file ID. """
        # Load fixture
        self.load_fixture([os.path.join(FIXTURES_DIR, "reingest-file-id.json")])
        # Verify METS state
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 1
        )
        # Run test
        mets = archivematicaCreateMETSReingest.update_object(
            Job("stub", "stub", []), mets
        )
        root = mets.serialize()
        assert (
            len(
                root.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 2
        )
        # Verify old techMD
        old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
        old_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
        )[0]
        assert old_techmd.attrib["STATUS"] == "superseded"
        namespaces = nsmap_for_premis2()
        assert (
            old_techmd.findtext(".//premis:formatName", namespaces=namespaces)
            == "JPEG 1.02"
        )
        assert (
            old_techmd.findtext(".//premis:formatVersion", namespaces=namespaces)
            == "1.02"
        )
        assert (
            old_techmd.findtext(".//premis:formatRegistryKey", namespaces=namespaces)
            == "fmt/44"
        )
        # Verify new techMD
        new_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
        )[0]
        assert new_techmd.attrib["STATUS"] == "current"
        assert (
            new_techmd.findtext(".//premis:formatName", namespaces=NSMAP)
            == "Newer fancier JPEG"
        )
        assert (
            new_techmd.findtext(".//premis:formatVersion", namespaces=NSMAP) == "9001"
        )
        assert (
            new_techmd.findtext(".//premis:formatRegistryKey", namespaces=NSMAP)
            == "fmt/9000"
        )
        # Verify rest of new techMD was created
        assert (
            new_techmd.find(".//premis:relatedObjectIdentifierType", namespaces=NSMAP)
            is not None
        )
        assert (
            len(
                new_techmd.find(
                    ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
                )
            )
            > 0
        )

    def test_update_characterization(self):
        """ It should add a new techMD with the new characterization. """
        # Load fixture
        self.load_fixture(
            [
                os.path.join(FIXTURES_DIR, f)
                for f in ["reingest-characterization.json", "fpr-reingest.json"]
            ]
        )
        # Verify METS state
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 1
        )
        # Run test
        mets = archivematicaCreateMETSReingest.update_object(
            Job("stub", "stub", []), mets
        )
        root = mets.serialize()
        assert (
            len(
                root.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 2
        )
        # Verify old techMD - fall back to PREMIS 2
        old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
        old_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
        )[0]
        assert old_techmd.attrib["STATUS"] == "superseded"
        namespaces = nsmap_for_premis2()
        assert (
            len(
                old_techmd.find(
                    ".//premis:objectCharacteristicsExtension", namespaces=namespaces
                )
            )
            == 3
        )
        # Verify new techMD
        new_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
        )[0]
        assert new_techmd.attrib["STATUS"] == "current"
        assert (
            len(
                new_techmd.find(
                    ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
                )
            )
            == 2
        )
        assert (
            new_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
            )[0].text
            == "Stub ffprobe output"
        )
        assert (
            new_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
            )[1].text
            == "Stub MediaInfo output"
        )
        # Verify rest of new techMD was created
        assert new_techmd.find(".//premis:formatName", namespaces=NSMAP) is not None
        assert (
            new_techmd.find(".//premis:relatedObjectIdentifierType", namespaces=NSMAP)
            is not None
        )

    def test_update_preservation_derivative(self):
        """ It should add a new techMD with the new relationship. """
        # Load fixture
        self.load_fixture([os.path.join(FIXTURES_DIR, "reingest-preservation.json")])
        # Verify METS state
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 1
        )
        # Run test
        mets = archivematicaCreateMETSReingest.update_object(
            Job("stub", "stub", []), mets
        )
        root = mets.serialize()
        assert (
            len(
                root.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 2
        )
        # Verify old techMD
        old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
        old_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
        )[0]
        assert old_techmd.attrib["STATUS"] == "superseded"
        namespaces = nsmap_for_premis2()
        assert (
            old_techmd.findtext(
                ".//premis:relatedObjectIdentifierValue", namespaces=namespaces
            )
            == "8140ebe5-295c-490b-a34a-83955b7c844e"
        )
        assert (
            old_techmd.findtext(
                ".//premis:relatedEventIdentifierValue", namespaces=namespaces
            )
            == "0ce13092-911f-4a89-b9e1-0e61921a03d4"
        )
        # Verify new techMD
        new_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
        )[0]
        assert new_techmd.attrib["STATUS"] == "current"
        assert (
            new_techmd.findtext(
                ".//premis:relatedObjectIdentifierValue", namespaces=NSMAP
            )
            == "d8cc7af7-284a-42f5-b7f4-e181a0efc35f"
        )
        assert (
            new_techmd.findtext(
                ".//premis:relatedEventIdentifierValue", namespaces=NSMAP
            )
            == "291f9be4-d19a-4bcc-8e1c-d3f01e4a48b1"
        )
        # Verify rest of new techMD was created
        assert new_techmd.find(".//premis:formatName", namespaces=NSMAP) is not None
        assert (
            new_techmd.find(".//premis:relatedObjectIdentifierType", namespaces=NSMAP)
            is not None
        )
        assert (
            len(
                new_techmd.find(
                    ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
                )
            )
            > 0
        )

    def test_update_all(self):
        """
        It should add new updated object and mark the old one as superseded.
        It should add after the last techMD.
        It should not modify other objects.
        It should have a new format identification event.
        """
        # Load fixture
        self.load_fixture(
            [
                os.path.join(FIXTURES_DIR, f)
                for f in [
                    "reingest-checksum.json",
                    "reingest-file-id.json",
                    "reingest-characterization.json",
                    "fpr-reingest.json",
                    "reingest-preservation.json",
                ]
            ]
        )
        models.File.objects.filter(uuid="ae8d4290-fe52-4954-b72a-0f591bee2e2f").update(
            checksumtype="md5", checksum="ac63a92ba5a94c337e740d6f189200d0"
        )
        # Verify METS state
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 1
        )
        # Run test
        mets = archivematicaCreateMETSReingest.update_object(
            Job("stub", "stub", []), mets
        )
        root = mets.serialize()
        assert (
            len(
                root.findall(
                    'mets:amdSec[@ID="amdSec_2"]//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
                    namespaces=NSMAP,
                )
            )
            == 2
        )
        # Verify old techMD
        old_techmd = root.find('.//mets:techMD[@ID="techMD_2"]', namespaces=NSMAP)
        old_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID="techMD_2"]', namespaces=NSMAP
        )[0]
        assert old_techmd.attrib["STATUS"] == "superseded"
        # Verify new techMD
        new_techmd = root.xpath(
            'mets:amdSec[@ID="amdSec_2"]/mets:techMD[@ID!="techMD_2"]', namespaces=NSMAP
        )[0]
        assert new_techmd.attrib["STATUS"] == "current"
        # Checksums
        assert (
            new_techmd.findtext(".//premis:messageDigestAlgorithm", namespaces=NSMAP)
            == "md5"
        )
        assert (
            new_techmd.findtext(".//premis:messageDigest", namespaces=NSMAP)
            == "ac63a92ba5a94c337e740d6f189200d0"
        )
        # File ID
        assert (
            new_techmd.findtext(".//premis:formatName", namespaces=NSMAP)
            == "Newer fancier JPEG"
        )
        assert (
            new_techmd.findtext(".//premis:formatVersion", namespaces=NSMAP) == "9001"
        )
        assert (
            new_techmd.findtext(".//premis:formatRegistryKey", namespaces=NSMAP)
            == "fmt/9000"
        )
        # Characterize
        assert (
            len(
                new_techmd.find(
                    ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
                )
            )
            == 2
        )
        assert (
            new_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
            )[0].text
            == "Stub ffprobe output"
        )
        assert (
            new_techmd.find(
                ".//premis:objectCharacteristicsExtension", namespaces=NSMAP
            )[1].text
            == "Stub MediaInfo output"
        )
        # Preservation
        assert (
            new_techmd.findtext(
                ".//premis:relatedObjectIdentifierValue", namespaces=NSMAP
            )
            == "d8cc7af7-284a-42f5-b7f4-e181a0efc35f"
        )
        assert (
            new_techmd.findtext(
                ".//premis:relatedEventIdentifierValue", namespaces=NSMAP
            )
            == "291f9be4-d19a-4bcc-8e1c-d3f01e4a48b1"
        )

    @unittest.expectedFailure
    def test_update_reingest_object(self):
        """
        It should add new updated object and mark all the old ones as superseded.
        It should add after the last techMD.
        """
        raise NotImplementedError()

    def test__update_premis_object(self):
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_namespaces.xml")
        )
        root = mets.serialize()

        for i in range(1, 4):
            path = (
                './/mets:techMD[@ID="techMD_{}"]'
                "/mets:mdWrap/mets:xmlData/premis:object".format(i)
            )
            premis_object = root.find(path, namespaces=nsmap_for_premis2())
            # This is what we're trying to avoid: PREMIS as the default ns.
            assert premis_object.nsmap[None] == "info:lc/xmlns/premis-v2"
            new = archivematicaCreateMETSReingest._update_premis_object(
                premis_object, "file"
            )
            # Previous element has been emptied.
            assert len(premis_object.getchildren()) == 0
            # It should not have a default namespace anymore.
            assert None not in new.nsmap
            # PREMIS should be using the ``premis`` prefix.
            assert new.nsmap["premis"] == "http://www.loc.gov/premis/v3"
            # Children have been incorporated into the new object.
            assert len(new.getchildren())
            # Subelements are prefixed too.
            assert len(new.find(".//premis:fixity", namespaces=NSMAP)) == 2


class TestUpdateDublinCore(TestCase):
    """ Test updating SIP-level DublinCore. (update_dublincore) """

    fixture_files = ["metadata_applies_to_type.json", "dublincore.json"]
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    sip_uuid_none = "dnedne7c-5bd2-4249-84a1-2f00f725b981"
    sip_uuid_original = "8b891d7c-5bd2-4249-84a1-2f00f725b981"
    sip_uuid_reingest = "87d30df4-63f5-434b-9da6-25aa995de6fe"
    sip_uuid_updated = "5d78a2a5-57a6-430f-87b2-b89fb3ccb050"

    def test_no_dc(self):
        """ It should do nothing if there is no DC entry. """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            mets.tree.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
            is None
        )
        mets = archivematicaCreateMETSReingest.update_dublincore(
            Job("stub", "stub", []), mets, self.sip_uuid_none
        )
        assert (
            mets.serialize().find(
                'mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP
            )
            is None
        )

    def test_dc_not_updated(self):
        """ It should do nothing if the DC has not been modified. """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            mets.tree.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
            is None
        )
        mets = archivematicaCreateMETSReingest.update_dublincore(
            Job("stub", "stub", []), mets, self.sip_uuid_reingest
        )
        assert (
            mets.serialize().find(
                'mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP
            )
            is None
        )

    def test_new_dc(self):
        """
        It should add a new DC if there was none before.
        It should add after the metsHdr if no dmdSecs exist.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            mets.tree.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
            is None
        )
        mets = archivematicaCreateMETSReingest.update_dublincore(
            Job("stub", "stub", []), mets, self.sip_uuid_original
        )
        root = mets.serialize()
        assert (
            root.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)
            is not None
        )
        dmdsec = root.find("mets:dmdSec", namespaces=NSMAP)
        assert dmdsec.attrib["CREATED"]
        # Verify fileSec div updated
        assert (
            root.find(
                'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
                namespaces=NSMAP,
            ).attrib["DMDID"]
            == dmdsec.attrib["ID"]
        )
        # Verify DC correct
        dc_elem = root.find(
            'mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]/mets:xmlData/dcterms:dublincore',
            namespaces=NSMAP,
        )
        assert len(dc_elem) == 15
        assert dc_elem[0].tag == "{http://purl.org/dc/elements/1.1/}title"
        assert dc_elem[0].text == "Yamani Weapons"
        assert dc_elem[1].tag == "{http://purl.org/dc/elements/1.1/}creator"
        assert dc_elem[1].text == "Keladry of Mindelan"
        assert dc_elem[2].tag == "{http://purl.org/dc/elements/1.1/}subject"
        assert dc_elem[2].text == "Glaives"
        assert dc_elem[3].tag == "{http://purl.org/dc/elements/1.1/}description"
        assert dc_elem[3].text == "Glaives are cool"
        assert dc_elem[4].tag == "{http://purl.org/dc/elements/1.1/}publisher"
        assert dc_elem[4].text == "Tortall Press"
        assert dc_elem[5].tag == "{http://purl.org/dc/elements/1.1/}contributor"
        assert dc_elem[5].text == "Yuki"
        assert dc_elem[6].tag == "{http://purl.org/dc/elements/1.1/}date"
        assert dc_elem[6].text == "2015"
        assert dc_elem[7].tag == "{http://purl.org/dc/elements/1.1/}type"
        assert dc_elem[7].text == "Archival Information Package"
        assert dc_elem[8].tag == "{http://purl.org/dc/elements/1.1/}format"
        assert dc_elem[8].text == "parchement"
        assert dc_elem[9].tag == "{http://purl.org/dc/elements/1.1/}identifier"
        assert dc_elem[9].text == "42/1"
        assert dc_elem[10].tag == "{http://purl.org/dc/elements/1.1/}source"
        assert dc_elem[10].text == "Numair's library"
        assert dc_elem[11].tag == "{http://purl.org/dc/elements/1.1/}relation"
        assert dc_elem[11].text == "None"
        assert dc_elem[12].tag == "{http://purl.org/dc/elements/1.1/}language"
        assert dc_elem[12].text == "en"
        assert dc_elem[13].tag == "{http://purl.org/dc/elements/1.1/}rights"
        assert dc_elem[13].text == "Public Domain"
        assert dc_elem[14].tag == "{http://purl.org/dc/terms/}isPartOf"
        assert dc_elem[14].text == "AIC#42"

    def test_update_existing_dc(self):
        """
        It should add a new updated DC and mark the old one as original.
        It should ignore file-level DC.
        It should add after the last dmdSec.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_sip_and_file_dc.xml")
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP
                )
            )
            == 4
        )
        mets = archivematicaCreateMETSReingest.update_dublincore(
            Job("stub", "stub", []), mets, self.sip_uuid_updated
        )
        root = mets.serialize()
        assert (
            len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP))
            == 5
        )
        # Verify file-level DC not updated
        assert (
            root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP).get("STATUS")
            is None
        )
        assert (
            root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP).get("STATUS")
            is None
        )
        assert (
            root.find('mets:dmdSec[@ID="dmdSec_3"]', namespaces=NSMAP).get("STATUS")
            is None
        )
        # Verify original SIP-level marked as original
        assert (
            root.find('mets:dmdSec[@ID="dmdSec_4"]', namespaces=NSMAP).attrib["STATUS"]
            == "original"
        )
        # Verify dmdSec created
        dmdsec = root.xpath(
            'mets:dmdSec[not(@ID="dmdSec_1" or @ID="dmdSec_2" or @ID="dmdSec_3" or @ID="dmdSec_4")]',
            namespaces=NSMAP,
        )[0]
        assert dmdsec.attrib["STATUS"] == "updated"
        assert dmdsec.attrib["CREATED"]
        # Verify fileSec div updated
        assert (
            dmdsec.attrib["ID"]
            in root.find(
                'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
                namespaces=NSMAP,
            ).attrib["DMDID"]
        )
        assert (
            "dmdSec_4"
            in root.find(
                'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
                namespaces=NSMAP,
            ).attrib["DMDID"]
        )
        # Verify new DC
        dc_elem = dmdsec.find(".//dcterms:dublincore", namespaces=NSMAP)
        assert len(dc_elem) == 12
        assert dc_elem[0].tag == "{http://purl.org/dc/elements/1.1/}title"
        assert dc_elem[0].text == "Yamani Weapons"
        assert dc_elem[1].tag == "{http://purl.org/dc/elements/1.1/}creator"
        assert dc_elem[1].text == "Keladry of Mindelan"
        assert dc_elem[2].tag == "{http://purl.org/dc/elements/1.1/}subject"
        assert dc_elem[2].text == "Glaives"
        assert dc_elem[3].tag == "{http://purl.org/dc/elements/1.1/}description"
        assert dc_elem[3].text == "Glaives are awesome"
        assert dc_elem[4].tag == "{http://purl.org/dc/elements/1.1/}publisher"
        assert dc_elem[4].text == "Tortall Press"
        assert dc_elem[5].tag == "{http://purl.org/dc/elements/1.1/}contributor"
        assert dc_elem[5].text == "Yuki, Neal"
        assert dc_elem[6].tag == "{http://purl.org/dc/elements/1.1/}type"
        assert dc_elem[6].text == "Archival Information Package"
        assert dc_elem[7].tag == "{http://purl.org/dc/elements/1.1/}format"
        assert dc_elem[7].text == "palimpsest"
        assert dc_elem[8].tag == "{http://purl.org/dc/elements/1.1/}identifier"
        assert dc_elem[8].text == "42/1"
        assert dc_elem[9].tag == "{http://purl.org/dc/elements/1.1/}language"
        assert dc_elem[9].text == "en"
        assert dc_elem[10].tag == "{http://purl.org/dc/elements/1.1/}coverage"
        assert dc_elem[10].text == "Partial"
        assert dc_elem[11].tag == "{http://purl.org/dc/elements/1.1/}rights"
        assert dc_elem[11].text == "Public Domain"

    def test_update_reingested_dc(self):
        """
        It should add a new DC if old ones exist.
        It should not mark other reingested DC as original.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_multiple_sip_dc.xml")
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP
                )
            )
            == 2
        )
        mets = archivematicaCreateMETSReingest.update_dublincore(
            Job("stub", "stub", []), mets, self.sip_uuid_updated
        )
        root = mets.serialize()
        assert (
            len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP))
            == 3
        )
        # Verify existing DC marked as original
        assert (
            root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP).get("STATUS")
            == "original"
        )
        assert (
            root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP).get("STATUS")
            == "updated"
        )
        # Verify dmdSec created
        dmdsec = root.xpath(
            'mets:dmdSec[not(@ID="dmdSec_1" or @ID="dmdSec_2")]', namespaces=NSMAP
        )[0]
        assert dmdsec.attrib["STATUS"] == "updated"
        assert dmdsec.attrib["CREATED"]
        # Verify fileSec div updated
        assert (
            dmdsec.attrib["ID"]
            in root.find(
                'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
                namespaces=NSMAP,
            ).attrib["DMDID"]
        )
        assert (
            "dmdSec_1"
            in root.find(
                'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
                namespaces=NSMAP,
            ).attrib["DMDID"]
        )
        assert (
            "dmdSec_2"
            in root.find(
                'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
                namespaces=NSMAP,
            ).attrib["DMDID"]
        )
        # Verify new DC
        dc_elem = dmdsec.find(".//dcterms:dublincore", namespaces=NSMAP)
        assert len(dc_elem) == 12
        assert dc_elem[0].tag == "{http://purl.org/dc/elements/1.1/}title"
        assert dc_elem[0].text == "Yamani Weapons"
        assert dc_elem[1].tag == "{http://purl.org/dc/elements/1.1/}creator"
        assert dc_elem[1].text == "Keladry of Mindelan"
        assert dc_elem[2].tag == "{http://purl.org/dc/elements/1.1/}subject"
        assert dc_elem[2].text == "Glaives"
        assert dc_elem[3].tag == "{http://purl.org/dc/elements/1.1/}description"
        assert dc_elem[3].text == "Glaives are awesome"
        assert dc_elem[4].tag == "{http://purl.org/dc/elements/1.1/}publisher"
        assert dc_elem[4].text == "Tortall Press"
        assert dc_elem[5].tag == "{http://purl.org/dc/elements/1.1/}contributor"
        assert dc_elem[5].text == "Yuki, Neal"
        assert dc_elem[6].tag == "{http://purl.org/dc/elements/1.1/}type"
        assert dc_elem[6].text == "Archival Information Package"
        assert dc_elem[7].tag == "{http://purl.org/dc/elements/1.1/}format"
        assert dc_elem[7].text == "palimpsest"
        assert dc_elem[8].tag == "{http://purl.org/dc/elements/1.1/}identifier"
        assert dc_elem[8].text == "42/1"
        assert dc_elem[9].tag == "{http://purl.org/dc/elements/1.1/}language"
        assert dc_elem[9].text == "en"
        assert dc_elem[10].tag == "{http://purl.org/dc/elements/1.1/}coverage"
        assert dc_elem[10].text == "Partial"
        assert dc_elem[11].tag == "{http://purl.org/dc/elements/1.1/}rights"
        assert dc_elem[11].text == "Public Domain"

    def test_delete_dc(self):
        """ It should create a new dmdSec with no values. """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_multiple_sip_dc.xml")
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP
                )
            )
            == 2
        )

        mets = archivematicaCreateMETSReingest.update_dublincore(
            Job("stub", "stub", []), mets, self.sip_uuid_none
        )
        root = mets.serialize()

        assert (
            len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP))
            == 3
        )
        # Verify existing DC marked as original
        assert (
            root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP).get("STATUS")
            == "original"
        )
        assert (
            root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP).get("STATUS")
            == "updated"
        )
        # Verify dmdSec created
        dmdsec = root.xpath(
            'mets:dmdSec[not(@ID="dmdSec_1" or @ID="dmdSec_2")]', namespaces=NSMAP
        )[0]
        assert dmdsec.attrib["STATUS"] == "updated"
        assert dmdsec.attrib["CREATED"]
        # Verify fileSec div updated
        assert (
            dmdsec.attrib["ID"]
            in root.find(
                'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
                namespaces=NSMAP,
            ).attrib["DMDID"]
        )
        assert (
            "dmdSec_1"
            in root.find(
                'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
                namespaces=NSMAP,
            ).attrib["DMDID"]
        )
        assert (
            "dmdSec_2"
            in root.find(
                'mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]',
                namespaces=NSMAP,
            ).attrib["DMDID"]
        )
        # Verify new DC
        dc_elem = dmdsec.find(".//dcterms:dublincore", namespaces=NSMAP)
        assert len(dc_elem) == 0


class TestUpdateRights(TestCase):
    """ Test updating PREMIS:RIGHTS. (update_rights and add_rights_elements) """

    fixture_files = ["metadata_applies_to_type.json", "rights.json"]
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    sip_uuid_none = "dnedne7c-5bd2-4249-84a1-2f00f725b981"
    sip_uuid_original = "a4a5480c-9f51-4119-8dcb-d3f12e647c14"
    sip_uuid_reingest = "10d57d98-29e5-4b2c-9f9f-d163e632eb31"
    sip_uuid_updated = "2941f14c-bd57-4f4a-a514-a3bf6ac5adf0"

    def test_no_rights(self):
        """ It should do nothing if there are no rights entries. """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert mets.tree.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_rights(
            Job("stub", "stub", []), mets, self.sip_uuid_none, state
        )
        root = mets.serialize()
        assert root.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None

    def test_rights_not_updated(self):
        """ It should do nothing if the rights have not been modified. """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert mets.tree.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_rights(
            Job("stub", "stub", []), mets, self.sip_uuid_reingest, state
        )
        root = mets.serialize()
        assert root.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None

    def test_new_rights(self):
        """
        It should add a new rights if there were none before.
        It should add after the last techMD.
        It should add rights to all original files.
        It should not add rights to the METS file amdSec.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert mets.tree.find("mets:amdSec/mets:rightsMD", namespaces=NSMAP) is None
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_rights(
            Job("stub", "stub", []), mets, self.sip_uuid_original, state
        )
        root = mets.serialize()

        # Verify new rightsMD for all rightsstatements
        assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 4
        # Verify all associated with the original file
        assert (
            len(
                root.findall(
                    'mets:amdSec[@ID="amdSec_2"]/mets:rightsMD', namespaces=NSMAP
                )
            )
            == 4
        )
        # Verify rightsMDs exist with correct basis
        assert (
            root.xpath('.//premis:rightsBasis[text()="Copyright"]', namespaces=NSMAP)[0]
            is not None
        )
        assert (
            root.xpath('.//premis:rightsBasis[text()="Statute"]', namespaces=NSMAP)[0]
            is not None
        )
        assert (
            root.xpath('.//premis:rightsBasis[text()="License"]', namespaces=NSMAP)[0]
            is not None
        )
        assert (
            root.xpath('.//premis:rightsBasis[text()="Other"]', namespaces=NSMAP)[0]
            is not None
        )

    def test_update_existing_rights(self):
        """
        It should add new updated rights and mark the old ones as superseded.
        It should add after the last rightsMD.
        It should add rights to all files.
        It should not add rights to the METS file.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_all_rights.xml")
        )
        assert (
            len(mets.tree.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 5
        )
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_rights(
            Job("stub", "stub", []), mets, self.sip_uuid_updated, state
        )
        root = mets.serialize()

        # Verify new rightsMD for all rightsstatements
        assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 6
        # Verify all associated with the original file
        assert (
            len(
                root.findall(
                    'mets:amdSec[@ID="amdSec_1"]/mets:rightsMD', namespaces=NSMAP
                )
            )
            == 6
        )
        assert (
            root.find(
                'mets:amdSec/mets:rightsMD[@ID="rightsMD_1"]', namespaces=NSMAP
            ).get("STATUS")
            is None
        )
        assert (
            root.find(
                'mets:amdSec/mets:rightsMD[@ID="rightsMD_2"]', namespaces=NSMAP
            ).attrib["STATUS"]
            == "superseded"
        )
        assert (
            root.find(
                'mets:amdSec/mets:rightsMD[@ID="rightsMD_3"]', namespaces=NSMAP
            ).get("STATUS")
            is None
        )
        assert (
            root.find(
                'mets:amdSec/mets:rightsMD[@ID="rightsMD_4"]', namespaces=NSMAP
            ).get("STATUS")
            is None
        )
        assert (
            root.find(
                'mets:amdSec/mets:rightsMD[@ID="rightsMD_5"]', namespaces=NSMAP
            ).get("STATUS")
            is None
        )
        new_rights = root.find('mets:amdSec[@ID="amdSec_1"]', namespaces=NSMAP)[6]
        assert new_rights is not None
        assert new_rights.attrib["STATUS"] == "current"
        assert new_rights.attrib["CREATED"]
        assert (
            new_rights.findtext(".//premis:rightsBasis", namespaces=NSMAP) == "Statute"
        )
        assert (
            new_rights.findtext(
                ".//premis:statuteApplicableDates/premis:endDate", namespaces=NSMAP
            )
            == "2054"
        )
        assert (
            new_rights.findtext(
                ".//premis:termOfRestriction/premis:endDate", namespaces=NSMAP
            )
            == "2054"
        )
        assert new_rights.findtext(".//premis:statuteNote", namespaces=NSMAP) == "SIN"

    def test_update_reingested_rights(self):
        """
        It should add new updated rights and mark all the old ones as superseded.
        It should add after the last rightsMD.
        It should add rights to all files.
        It should not add rights to the METS file.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_updated_rights.xml")
        )
        assert (
            len(mets.tree.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 2
        )
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_rights(
            Job("stub", "stub", []), mets, self.sip_uuid_updated, state
        )
        root = mets.serialize()

        # Verify new rightsMD for all rightsstatements
        assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 3
        # Verify all associated with the original file
        assert (
            len(
                root.findall(
                    'mets:amdSec[@ID="amdSec_1"]/mets:rightsMD', namespaces=NSMAP
                )
            )
            == 3
        )
        assert (
            root.find(
                'mets:amdSec/mets:rightsMD[@ID="rightsMD_1"]', namespaces=NSMAP
            ).attrib["STATUS"]
            == "superseded"
        )
        assert (
            root.find(
                'mets:amdSec/mets:rightsMD[@ID="rightsMD_2"]', namespaces=NSMAP
            ).attrib["STATUS"]
            == "superseded"
        )
        new_rights = root.find('mets:amdSec[@ID="amdSec_1"]', namespaces=NSMAP)[3]
        assert new_rights is not None
        assert new_rights.attrib["STATUS"] == "current"
        assert new_rights.attrib["CREATED"]
        assert (
            new_rights.find(
                ".//premis:statuteApplicableDates/premis:endDate", namespaces=NSMAP
            ).text
            == "2054"
        )
        assert (
            new_rights.find(
                ".//premis:termOfRestriction/premis:endDate", namespaces=NSMAP
            ).text
            == "2054"
        )
        assert new_rights.find(".//premis:statuteNote", namespaces=NSMAP).text == "SIN"

    def test_delete_rights(self):
        """ It should mark the original rightsMD as obsolete. """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_all_rights.xml")
        )
        assert (
            len(mets.tree.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 5
        )
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_rights(
            Job("stub", "stub", []), mets, self.sip_uuid_none, state
        )
        root = mets.serialize()

        assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 5
        assert (
            len(
                root.findall(
                    'mets:amdSec/mets:rightsMD[@STATUS="superseded"]', namespaces=NSMAP
                )
            )
            == 5
        )

    def test_delete_and_add(self):
        """
        Use case: Entire rights basis deleted, new one added
        Solution: Mark original rightsMD as superseded. New rightsMD marked as current.
        It should mark the original rightsMD as obsolete.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_updated_rights.xml")
        )
        assert (
            len(mets.tree.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 2
        )
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_rights(
            Job("stub", "stub", []), mets, self.sip_uuid_original, state
        )
        root = mets.serialize()

        assert len(root.findall("mets:amdSec/mets:rightsMD", namespaces=NSMAP)) == 6
        assert (
            len(
                root.findall(
                    'mets:amdSec/mets:rightsMD[@STATUS="superseded"]', namespaces=NSMAP
                )
            )
            == 2
        )
        assert (
            root.find(
                'mets:amdSec/mets:rightsMD[@ID="rightsMD_1"]', namespaces=NSMAP
            ).attrib["STATUS"]
            == "superseded"
        )
        assert (
            root.find(
                'mets:amdSec/mets:rightsMD[@ID="rightsMD_2"]', namespaces=NSMAP
            ).attrib["STATUS"]
            == "superseded"
        )
        assert (
            len(
                root.findall(
                    'mets:amdSec/mets:rightsMD[@STATUS="current"]', namespaces=NSMAP
                )
            )
            == 4
        )
        assert (
            root.xpath(
                'mets:amdSec/mets:rightsMD[@STATUS="current"]//premis:rightsBasis[text()="Statute"]',
                namespaces=NSMAP,
            )
            != []
        )


class TestAddEvents(TestCase):
    """ Test adding reingest events to all existing files. (add_events) """

    fixture_files = [
        "sip-reingest.json",
        "files.json",
        "agents.json",
        "events-reingest.json",
    ]
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"

    def test_all_files_get_events(self):
        """
        It should add reingestion events to all files.
        It should add deletion events only to deleted files.
        It should add new format identification, normalization, fixity check events to the original object.
        It should not change Agent information.
        """
        models.Agent.objects.all().delete()
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        num_events = models.Event.objects.count()
        assert (
            len(
                mets.tree.findall(
                    './/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP
                )
            )
            == 16
        )
        assert (
            len(
                mets.tree.findall(
                    './/mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP
                )
            )
            == 9
        )
        mets = archivematicaCreateMETSReingest.add_events(
            Job("stub", "stub", []), mets, self.sip_uuid
        )
        root = mets.serialize()
        assert (
            len(
                root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP)
            )
            == 16 + num_events
        )
        # Preservation
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="reingestion"]',
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="deletion"]',
                namespaces=NSMAP,
            )
            != []
        )
        # Original object
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="reingestion"]',
                namespaces=NSMAP,
            )
            != []
        )
        namespaces = nsmap_for_premis2()
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="format identification"]',
                namespaces=namespaces,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="normalization"]',
                namespaces=namespaces,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="fixity check"]',
                namespaces=namespaces,
            )
            != []
        )
        # Transfer METS
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_3"]//premis:eventType[text()="reingestion"]',
                namespaces=NSMAP,
            )
            != []
        )
        # Agents
        assert (
            len(
                root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP)
            )
            == 12
        )

    def test_agent_not_in_mets(self):
        """
        It should add a new Agent if it doesn't already exist.
        It should only add one new Agent even if multiple Events are added.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        num_events = models.Event.objects.count()
        assert (
            len(
                mets.tree.findall(
                    './/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP
                )
            )
            == 16
        )
        assert (
            len(
                mets.tree.findall(
                    './/mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP
                )
            )
            == 9
        )
        models.Agent.objects.filter(
            identifiertype="repository code", agenttype="organization"
        ).update(identifiervalue="new-repo-code")
        nsmap_v2 = nsmap_for_premis2()
        mets = archivematicaCreateMETSReingest.add_events(
            Job("stub", "stub", []), mets, self.sip_uuid
        )
        root = mets.serialize()
        assert (
            len(
                root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP)
            )
            == 16 + num_events
        )
        assert (
            len(
                root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP)
            )
            == 15
        )
        # Preservation
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="reingestion"]',
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="deletion"]',
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_1"]//premis:agentIdentifierValue[text()="%s"]'
                % get_preservation_system_identifier(),
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_1"]//premis:agentIdentifierValue[text()="demo"]',
                namespaces=nsmap_v2,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_1"]//premis:agentIdentifierValue[text()="new-repo-code"]',
                namespaces=NSMAP,
            )
            != []
        )
        # Original
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="reingestion"]',
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="format identification"]',
                namespaces=nsmap_v2,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="normalization"]',
                namespaces=nsmap_v2,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="fixity check"]',
                namespaces=nsmap_v2,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:agentIdentifierValue[text()="%s"]'
                % get_preservation_system_identifier(),
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:agentIdentifierValue[text()="demo"]',
                namespaces=nsmap_v2,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_2"]//premis:agentIdentifierValue[text()="new-repo-code"]',
                namespaces=NSMAP,
            )
            != []
        )
        # Transfer METS
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_3"]//premis:eventType[text()="reingestion"]',
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_3"]//premis:agentIdentifierValue[text()="%s"]'
                % get_preservation_system_identifier(),
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_3"]//premis:agentIdentifierValue[text()="demo"]',
                namespaces=nsmap_v2,
            )
            != []
        )
        assert (
            root.xpath(
                'mets:amdSec[@ID="amdSec_3"]//premis:agentIdentifierValue[text()="new-repo-code"]',
                namespaces=NSMAP,
            )
            != []
        )


class TestAddingNewFiles(TestCase):
    """ Test adding new metadata files to the structMap & fileSec. (add_new_files) """

    fixture_files = [
        "sip-reingest.json",
        "files.json",
        "reingest-preservation.json",
        "agents.json",
    ]
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"

    def test_no_new_files(self):
        """ It should not modify the fileSec or structMap if there are no new files. """
        # Make sure directory is empty
        sip_dir = Path(tempfile.mkdtemp()) / "emptysip"
        try:
            shutil.copytree(
                os.path.join(THIS_DIR, "fixtures", "emptysip"), str(sip_dir)
            )
            # Make sure directory is empty
            (sip_dir / "objects/metadata/transfers/.gitignore").unlink()

            mets = metsrw.METSDocument.fromfile(
                os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
            )
            assert len(mets.tree.findall("mets:amdSec", namespaces=NSMAP)) == 3
            assert (
                len(mets.tree.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
            )
            assert (
                mets.tree.find(
                    'mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP
                )
                is None
            )
            assert (
                len(
                    mets.tree.findall(
                        'mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP
                    )
                )
                == 10
            )

            mets = archivematicaCreateMETSReingest.add_new_files(
                Job("stub", "stub", []), mets, self.sip_uuid, str(sip_dir)
            )
            root = mets.serialize()
            assert len(root.findall("mets:amdSec", namespaces=NSMAP)) == 3
            assert len(root.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
            assert (
                root.find(
                    'mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP
                )
                is None
            )

            # There used to be 10 <mets:div> elements under the physical structMap.
            # However, now metsrw does not list empty directories (or directories
            # that only contain empty directories) in the physical structMap.
            # Therefore, the directories in the following path will not be
            # documented after metsrw has re-serialized:
            # metadata/transfers/no-metadata-46260807-ece1-4a0e-b70a-9814c701146b/
            assert (
                len(
                    root.findall(
                        'mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP
                    )
                )
                == 7
            )

        finally:
            shutil.rmtree(str(sip_dir.parent))

    def test_add_metadata_csv(self):
        """
        It should add a metadata file to the fileSec, structMap & amdSec.
        It should add a dmdSec.  (Other testing for TestUpdateMetadataCSV)
        """
        sip_dir = os.path.join(FIXTURES_DIR, "metadata_csv_sip", "")
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert len(mets.tree.findall("mets:amdSec", namespaces=NSMAP)) == 3
        assert len(mets.tree.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
        assert (
            mets.tree.find(
                'mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP
            )
            is None
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP
                )
            )
            == 10
        )

        mets = archivematicaCreateMETSReingest.add_new_files(
            Job("stub", "stub", []), mets, self.sip_uuid, sip_dir
        )

        file_uuid = "66370f14-2f64-4750-9d50-547614be40e8"
        root = mets.serialize()
        # Check structMap
        div = root.find(
            'mets:structMap/mets:div/mets:div[@LABEL="objects"]/mets:div[@LABEL="metadata"]/mets:div[@TYPE="Item"]',
            namespaces=NSMAP,
        )
        assert div is not None
        assert div.attrib["LABEL"] == "metadata.csv"
        assert len(div) == 1
        assert div[0].tag == "{http://www.loc.gov/METS/}fptr"
        assert div[0].attrib["FILEID"] == "file-" + file_uuid
        # Check fileSec
        mets_grp = root.find(
            'mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP
        )
        assert mets_grp is not None
        assert len(mets_grp) == 1
        assert mets_grp[0].tag == "{http://www.loc.gov/METS/}file"
        assert mets_grp[0].attrib["ID"] == "file-" + file_uuid
        assert mets_grp[0].attrib["GROUPID"] == "Group-" + file_uuid
        adm_id = mets_grp[0].attrib["ADMID"]
        assert adm_id
        assert len(mets_grp[0]) == 1
        assert mets_grp[0][0].tag == "{http://www.loc.gov/METS/}FLocat"
        assert mets_grp[0][0].attrib["LOCTYPE"] == "OTHER"
        assert mets_grp[0][0].attrib["OTHERLOCTYPE"] == "SYSTEM"
        assert (
            mets_grp[0][0].attrib["{http://www.w3.org/1999/xlink}href"]
            == "objects/metadata/metadata.csv"
        )
        # Check amdSec
        amdsec = root.find('mets:amdSec[@ID="' + adm_id + '"]', namespaces=NSMAP)
        assert amdsec is not None
        assert (
            amdsec.findtext(".//premis:objectIdentifierValue", namespaces=NSMAP)
            == file_uuid
        )
        assert (
            amdsec.findtext(".//premis:messageDigest", namespaces=NSMAP)
            == "e8121d8a660e2992872f0b67923d2d08dde9a1ba72dfd58e5a31e68fbac3633c"
        )
        assert amdsec.findtext(".//premis:size", namespaces=NSMAP) == "154"
        assert (
            amdsec.findtext(".//premis:originalName", namespaces=NSMAP)
            == "%SIPDirectory%metadata/metadata.csv"
        )

    def test_new_metadata_file_in_subdir(self):
        """ It should add the new subdirs to the structMap. """
        sip_dir = os.path.join(FIXTURES_DIR, "metadata_file_in_subdir_sip", "")
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert len(mets.tree.findall("mets:amdSec", namespaces=NSMAP)) == 3
        assert len(mets.tree.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
        assert (
            mets.tree.find(
                'mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP
            )
            is None
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP
                )
            )
            == 10
        )

        mets = archivematicaCreateMETSReingest.add_new_files(
            Job("stub", "stub", []), mets, self.sip_uuid, sip_dir
        )

        file_uuid = "950253b2-e5b1-4222-bb86-4eb436af5713"
        root = mets.serialize()
        # Check structMap
        # Dir
        div = root.find(
            'mets:structMap/mets:div/mets:div[@LABEL="objects"]/mets:div[@LABEL="metadata"]/mets:div[@LABEL="foo"]',
            namespaces=NSMAP,
        )
        assert div is not None
        assert len(div) == 1
        # File
        div = root.find(
            'mets:structMap/mets:div/mets:div[@LABEL="objects"]/mets:div[@LABEL="metadata"]/mets:div/mets:div[@TYPE="Item"]',
            namespaces=NSMAP,
        )
        assert div is not None
        assert div.attrib["LABEL"] == "foo.txt"
        assert len(div) == 1
        assert div[0].tag == "{http://www.loc.gov/METS/}fptr"
        assert div[0].attrib["FILEID"] == "file-" + file_uuid
        # Check fileSec
        mets_grp = root.find(
            'mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP
        )
        assert mets_grp is not None
        assert len(mets_grp) == 1
        assert mets_grp[0].tag == "{http://www.loc.gov/METS/}file"
        assert mets_grp[0].attrib["ID"] == "file-" + file_uuid
        assert mets_grp[0].attrib["GROUPID"] == "Group-" + file_uuid
        adm_id = mets_grp[0].attrib["ADMID"]
        assert adm_id
        assert len(mets_grp[0]) == 1
        assert mets_grp[0][0].tag == "{http://www.loc.gov/METS/}FLocat"
        assert mets_grp[0][0].attrib["LOCTYPE"] == "OTHER"
        assert mets_grp[0][0].attrib["OTHERLOCTYPE"] == "SYSTEM"
        assert (
            mets_grp[0][0].attrib["{http://www.w3.org/1999/xlink}href"]
            == "objects/metadata/foo/foo.txt"
        )
        # Check amdSec
        amdsec = root.find('mets:amdSec[@ID="' + adm_id + '"]', namespaces=NSMAP)
        assert amdsec is not None
        assert (
            amdsec.findtext(".//premis:objectIdentifierValue", namespaces=NSMAP)
            == file_uuid
        )

    def test_new_preservation_file(self):
        """
        It should add an amdSec for the new file.
        It should not have a reingestion event.
        It should add the new file to the fileSec under 'preservation'.
        It should add the new file to the structMap.
        Done elsewhere:
        update_object creates a new relationship in the original object.
        add_events adds a new normalization event to the original object.
        delete_files moves the old preservation object to 'deleted' fileGrp
        """
        # Verify existing
        file_uuid = "d8cc7af7-284a-42f5-b7f4-e181a0efc35f"
        original_file_uuid = "ae8d4290-fe52-4954-b72a-0f591bee2e2f"
        file_path = "evelyn_s_photo-d8cc7af7-284a-42f5-b7f4-e181a0efc35f.tif"
        sip_dir = os.path.join(FIXTURES_DIR, "new_preservation_file", "")
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert len(mets.tree.findall("mets:amdSec", namespaces=NSMAP)) == 3
        assert len(mets.tree.findall("mets:fileSec//mets:file", namespaces=NSMAP)) == 3
        assert (
            len(
                mets.tree.find(
                    'mets:fileSec/mets:fileGrp[@USE="preservation"]', namespaces=NSMAP
                )
            )
            == 1
        )
        assert (
            len(
                mets.tree.findall(
                    'mets:structMap[@TYPE="physical"]//mets:div', namespaces=NSMAP
                )
            )
            == 10
        )
        # Run test
        mets = archivematicaCreateMETSReingest.add_new_files(
            Job("stub", "stub", []), mets, self.sip_uuid, sip_dir
        )
        root = mets.serialize()
        # Check fileSec
        mets_grp = root.find(
            'mets:fileSec/mets:fileGrp[@USE="preservation"]', namespaces=NSMAP
        )
        assert len(mets_grp) == 2
        file_ = mets_grp.find(
            'mets:file[@ID="file-' + file_uuid + '"]', namespaces=NSMAP
        )
        assert file_.attrib["GROUPID"] == "Group-" + original_file_uuid
        adm_id = file_.attrib["ADMID"]
        assert adm_id
        assert len(file_) == 1
        assert file_[0].tag == "{http://www.loc.gov/METS/}FLocat"
        assert file_[0].attrib["LOCTYPE"] == "OTHER"
        assert file_[0].attrib["OTHERLOCTYPE"] == "SYSTEM"
        assert (
            file_[0].attrib["{http://www.w3.org/1999/xlink}href"]
            == "objects/evelyn_s_photo-d8cc7af7-284a-42f5-b7f4-e181a0efc35f.tif"
        )
        # Check structMap
        div = root.find(
            'mets:structMap/mets:div/mets:div[@LABEL="objects"]/mets:div[@LABEL="'
            + file_path
            + '"]',
            namespaces=NSMAP,
        )
        assert div is not None
        assert div.attrib["TYPE"] == "Item"
        assert len(div) == 1
        assert div[0].tag == "{http://www.loc.gov/METS/}fptr"
        assert div[0].attrib["FILEID"] == "file-" + file_uuid
        # Check amdSec
        assert len(root.findall("mets:amdSec", namespaces=NSMAP)) == 4
        amdsec = root.find('mets:amdSec[@ID="' + adm_id + '"]', namespaces=NSMAP)
        assert amdsec is not None
        # Check techMD
        premis_object = amdsec.find(".//premis:object", namespaces=NSMAP)
        assert premis_object is not None
        assert (
            premis_object.findtext(".//premis:objectIdentifierValue", namespaces=NSMAP)
            == file_uuid
        )
        assert (
            premis_object.findtext(".//premis:messageDigestAlgorithm", namespaces=NSMAP)
            == "sha256"
        )
        assert (
            premis_object.findtext(".//premis:messageDigest", namespaces=NSMAP)
            == "d82448f154b9185bc777ecb0a3602760eb76ba85dd3098f073b2c91a03f571e9"
        )
        assert premis_object.findtext(".//premis:size", namespaces=NSMAP) == "1446772"
        assert (
            premis_object.findtext(".//premis:formatName", namespaces=NSMAP) == "TIFF"
        )
        assert (
            premis_object.findtext(".//premis:originalName", namespaces=NSMAP)
            == "%SIPDirectory%objects/evelyn_s_photo-d8cc7af7-284a-42f5-b7f4-e181a0efc35f.tif"
        )
        assert (
            premis_object.findtext(".//premis:relationshipType", namespaces=NSMAP)
            == "derivation"
        )
        assert (
            premis_object.findtext(".//premis:relationshipSubType", namespaces=NSMAP)
            == "has source"
        )
        assert (
            premis_object.findtext(
                ".//premis:relatedObjectIdentifierValue", namespaces=NSMAP
            )
            == original_file_uuid
        )
        assert (
            premis_object.findtext(
                ".//premis:relatedEventIdentifierValue", namespaces=NSMAP
            )
            == "291f9be4-d19a-4bcc-8e1c-d3f01e4a48b1"
        )
        # Events: creation, message digest calculation, fixity check
        assert (
            amdsec.xpath('.//premis:eventType[text()="creation"]', namespaces=NSMAP)
            != []
        )
        assert (
            amdsec.xpath(
                './/premis:eventType[text()="message digest calculation"]',
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            amdsec.xpath('.//premis:eventType[text()="fixity check"]', namespaces=NSMAP)
            != []
        )
        # Agents
        assert (
            amdsec.xpath(
                './/premis:agentIdentifierValue[text()="%s"]'
                % get_preservation_system_identifier(),
                namespaces=NSMAP,
            )
            != []
        )
        assert (
            amdsec.xpath(
                './/premis:agentIdentifierValue[text()="demo"]', namespaces=NSMAP
            )
            != []
        )
        assert (
            amdsec.xpath(
                """.//premis:agentName[text()='username="kmindelan", first_name="Keladry", last_name="Mindelan"']""",
                namespaces=NSMAP,
            )
            != []
        )


class TestDeleteFiles(TestCase):
    """ Test marking files in the METS as deleted. (delete_files) """

    fixture_files = ["sip-reingest.json", "files.json", "events-reingest.json"]
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"

    def test_delete_file(self):
        """
        It should change the fileGrp USE to deleted.
        It should remove the FLocat from the fileSec.
        It should remove the div from the structMap.
        It should add a deletion event (covered by add_events).
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert (
            mets.tree.find('.//mets:fileGrp[@USE="preservation"]', namespaces=NSMAP)
            is not None
        )
        assert (
            mets.tree.find('.//mets:fileGrp[@USE="deleted"]', namespaces=NSMAP) is None
        )
        assert (
            mets.tree.find(
                './/mets:file[@ID="file-8140ebe5-295c-490b-a34a-83955b7c844e"]',
                namespaces=NSMAP,
            )
            is not None
        )
        assert (
            mets.tree.find(
                './/mets:FLocat[@xlink:href="objects/evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif"]',
                namespaces=NSMAP,
            )
            is not None
        )
        assert (
            mets.tree.find(
                './/mets:div[@LABEL="evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif"]',
                namespaces=NSMAP,
            )
            is not None
        )

        mets = archivematicaCreateMETSReingest.delete_files(mets, self.sip_uuid)
        root = mets.serialize()

        assert (
            root.find('.//mets:fileGrp[@USE="preservation"]', namespaces=NSMAP) is None
        )
        deletedgrp = root.find('.//mets:fileGrp[@USE="deleted"]', namespaces=NSMAP)
        assert deletedgrp is not None
        assert len(deletedgrp) == 1
        assert deletedgrp[0].tag == "{http://www.loc.gov/METS/}file"
        assert deletedgrp[0].attrib["ID"] == "file-8140ebe5-295c-490b-a34a-83955b7c844e"
        assert (
            deletedgrp[0].attrib["GROUPID"]
            == "Group-ae8d4290-fe52-4954-b72a-0f591bee2e2f"
        )
        assert deletedgrp[0].attrib["ADMID"] == "amdSec_1"
        assert len(deletedgrp[0].attrib) == 3
        assert len(deletedgrp[0]) == 0
        assert (
            root.find(
                './/mets:div[@LABEL="evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif"]',
                namespaces=NSMAP,
            )
            is None
        )


class TestUpdateMetadataCSV(TestCase):
    """ Test adding metadata.csv-based DC metadata. (update_metadata_csv) """

    fixture_files = ["sip-reingest.json", "files.json"]
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
    sip_dir = os.path.join(FIXTURES_DIR, "metadata_csv_sip", "")

    def setUp(self):
        self.csv_file = models.File.objects.get(
            uuid="66370f14-2f64-4750-9d50-547614be40e8"
        )

    def test_new_dmdsecs(self):
        """ It should add file-level dmdSecs. """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert len(mets.tree.findall("mets:dmdSec", namespaces=NSMAP)) == 0
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_metadata_csv(
            Job("stub", "stub", []),
            mets,
            self.csv_file,
            self.sip_uuid,
            self.sip_dir,
            state,
        )
        root = mets.serialize()
        assert len(root.findall("mets:dmdSec", namespaces=NSMAP)) == 1
        dmdsec = root.find("mets:dmdSec", namespaces=NSMAP)
        assert dmdsec.attrib["ID"]
        assert dmdsec.attrib["CREATED"]
        assert dmdsec.attrib["STATUS"] == "original"
        assert dmdsec.findtext(".//dc:title", namespaces=NSMAP) == "Mountain Tents"
        assert (
            dmdsec.findtext(".//dc:description", namespaces=NSMAP)
            == "Tents on a mountain"
        )

    def test_new_dmdsecs_for_directories(self):
        """ It should add directory-level dmdSecs. """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_sip_and_file_dc.xml")
        )
        assert not mets.get_file(label="Landing_zone", type="Directory").dmdsecs
        # Import metadata for the objects/Landing_zone directory
        # from fixtures/metadata_csv_directories/objects/metadata/metadata.csv
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        sip_dir = os.path.join(FIXTURES_DIR, "metadata_csv_directories", "")
        mets = archivematicaCreateMETSReingest.update_metadata_csv(
            Job("stub", "stub", []), mets, self.csv_file, self.sip_uuid, sip_dir, state
        )
        # Verify the new dmdSec for the Landing_zone directory
        assert len(mets.get_file(label="Landing_zone", type="Directory").dmdsecs) == 1
        dmdsec = (
            mets.get_file(label="Landing_zone", type="Directory").dmdsecs[0].serialize()
        )
        dmdsec.findtext(".//dc:title", namespaces=NSMAP) == "The landing zone"
        dmdsec.findtext(".//dc:description", namespaces=NSMAP) == "A zone for landing"

    def test_update_existing(self):
        """
        It should add new dmdSecs.
        It should updated the existing dmdSec as original.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_file_dc.xml")
        )
        assert len(mets.tree.findall("mets:dmdSec", namespaces=NSMAP)) == 1
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_metadata_csv(
            Job("stub", "stub", []),
            mets,
            self.csv_file,
            self.sip_uuid,
            self.sip_dir,
            state,
        )
        root = mets.serialize()
        assert len(root.findall("mets:dmdSec", namespaces=NSMAP)) == 2
        orig = root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP)
        assert orig.attrib["STATUS"] == "original"
        div = root.xpath('.//mets:div[contains(@DMDID,"dmdSec_1")]', namespaces=NSMAP)[
            0
        ]
        assert div.attrib["DMDID"]
        dmdid = div.attrib["DMDID"].split()[1]
        new = root.find('mets:dmdSec[@ID="' + dmdid + '"]', namespaces=NSMAP)
        assert new.attrib["CREATED"]
        assert new.attrib["STATUS"] == "updated"
        assert new.findtext(".//dc:title", namespaces=NSMAP) == "Mountain Tents"
        assert (
            new.findtext(".//dc:description", namespaces=NSMAP) == "Tents on a mountain"
        )

    def test_update_reingest(self):
        """
        It should add new dmdSecs.
        It should not updated the already updated dmdSecs.
        """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_file_dc_updated.xml")
        )
        assert len(mets.tree.findall("mets:dmdSec", namespaces=NSMAP)) == 2
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        mets = archivematicaCreateMETSReingest.update_metadata_csv(
            Job("stub", "stub", []),
            mets,
            self.csv_file,
            self.sip_uuid,
            self.sip_dir,
            state,
        )
        root = mets.serialize()
        assert len(root.findall("mets:dmdSec", namespaces=NSMAP)) == 3
        orig = root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP)
        assert orig.attrib["STATUS"] == "original"
        updated = root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP)
        assert updated.attrib["STATUS"] == "updated"
        div = root.xpath('.//mets:div[contains(@DMDID,"dmdSec_1")]', namespaces=NSMAP)[
            0
        ]
        assert div.attrib["DMDID"]
        dmdid = div.attrib["DMDID"].split()[2]
        new = root.find('mets:dmdSec[@ID="' + dmdid + '"]', namespaces=NSMAP)
        assert new.attrib["CREATED"]
        assert new.attrib["STATUS"] == "updated"
        assert new.findtext(".//dc:title", namespaces=NSMAP) == "Mountain Tents"
        assert (
            new.findtext(".//dc:description", namespaces=NSMAP) == "Tents on a mountain"
        )

    def test_non_dublincore_dmdsecs(self):
        """ It should add file-level dmdSecs for non DC metadata. """
        mets = metsrw.METSDocument.fromfile(
            os.path.join(FIXTURES_DIR, "mets_no_metadata.xml")
        )
        assert not mets.get_file(path="objects/evelyn_s_photo.jpg", type="Item").dmdsecs
        # Import DC and non DC metadata for the objects/evelyn_s_photo.jpg file
        # from fixtures/metadata_csv_nondc/objects/metadata/metadata.csv
        state = archivematicaCreateMETSReingest.createmets2.MetsState()
        sip_dir = os.path.join(FIXTURES_DIR, "metadata_csv_nondc", "")
        mets = archivematicaCreateMETSReingest.update_metadata_csv(
            Job("stub", "stub", []), mets, self.csv_file, self.sip_uuid, sip_dir, state
        )
        # Verify the new dmdSecs for the objects/evelyn_s_photo.jpg file
        assert (
            len(mets.get_file(path="objects/evelyn_s_photo.jpg", type="Item").dmdsecs)
            == 2
        )
        dmdsecs = [
            dmdsec.serialize()
            for dmdsec in mets.get_file(
                path="objects/evelyn_s_photo.jpg", type="Item"
            ).dmdsecs
        ]
        # There should be one DC dmdsec
        dc_dmdsecs = [
            dmdsec
            for dmdsec in dmdsecs
            if dmdsec.find(".//dcterms:dublincore", namespaces=NSMAP) is not None
        ]
        assert len(dc_dmdsecs) == 1
        assert (
            dc_dmdsecs[0].findtext(".//dc:title", namespaces=NSMAP) == "Mountain Tents"
        )
        assert (
            dc_dmdsecs[0].findtext(".//dc:description", namespaces=NSMAP)
            == "Tents on a mountain"
        )
        # And one non DC dmdsec
        nondc_dmdsecs = [
            dmdsec
            for dmdsec in dmdsecs
            if dmdsec.find(
                './/mets:mdWrap[@MDTYPE="OTHER"][@OTHERMDTYPE="CUSTOM"]/mets:xmlData',
                namespaces=NSMAP,
            )
            is not None
        ]
        assert len(nondc_dmdsecs) == 1
        assert (
            nondc_dmdsecs[0].findtext(".//nondc", namespaces=NSMAP) == "Non DC metadata"
        )
        assert (
            nondc_dmdsecs[0].findtext(".//custom_field", namespaces=NSMAP)
            == "A custom field"
        )
