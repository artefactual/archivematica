# -*- coding: utf8
from __future__ import unicode_literals
import collections
import csv
import os
import random
import shutil
import sys
import tempfile
import unittest

import scandir
from django.test import TestCase

from lxml import etree
from six.moves import range
import six

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
sys.path.append(
    os.path.abspath(os.path.join(THIS_DIR, "../../archivematicaCommon/lib"))
)

from job import Job
import create_mets_v2
import archivematicaCreateMETSMetadataCSV
import archivematicaCreateMETSRights

from main.models import RightsStatement
from . import TempDirMixin

import namespaces as ns
from version import get_preservation_system_identifier

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

# XXX we can probably replace this given the am common import...
NSMAP = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "mets": "http://www.loc.gov/METS/",
    "premis": "http://www.loc.gov/premis/v3",
}


class TestNormativeStructMap(TempDirMixin, TestCase):
    """Test creation of normative structMap."""

    fixture_files = []
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def setUp(self):
        super(TestNormativeStructMap, self).setUp()
        self.sip_dir = self.tmpdir / "sip"
        self.sip_object_dir = self.sip_dir / "objects"
        shutil.copytree(
            os.path.join(THIS_DIR, "fixtures", "create_aip_mets", ""), str(self.sip_dir)
        )

    def test_path_to_fsitems(self):
        """It should return 4 tuple instances"""
        (self.sip_object_dir / "empty_dir").mkdir()
        fsitems = create_mets_v2.get_paths_as_fsitems(
            str(self.sip_dir) + os.sep, str(self.sip_object_dir)
        )
        assert len(fsitems) == 4
        assert isinstance(fsitems[0], tuple)
        assert isinstance(fsitems[1], tuple)
        assert isinstance(fsitems[2], tuple)
        assert isinstance(fsitems[3], tuple)

    def test_normative_structmap_creation(self):
        """It should return an etree Element instance."""
        state = create_mets_v2.MetsState()
        normativeStructMap = create_mets_v2.get_normative_structmap(
            str(self.sip_dir) + os.sep, str(self.sip_object_dir), {}, state
        )
        assert isinstance(normativeStructMap, etree._Element)


class TestDublinCore(TestCase):
    """Test creation of dmdSecs containing Dublin Core."""

    fixture_files = ["metadata_applies_to_type.json", "dublincore.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]
    sipuuid = "8b891d7c-5bd2-4249-84a1-2f00f725b981"
    siptypeuuid = "3e48343d-e2d2-4956-aaa3-b54d26eb9761"

    def test_get_dublincore(self):
        """It should create a Dublin Core element from the database info."""
        # Generate DC element from DB
        dc_elem = create_mets_v2.getDublinCore(self.siptypeuuid, self.sipuuid)

        # Verify created correctly
        assert dc_elem is not None
        assert dc_elem.tag == "{http://purl.org/dc/terms/}dublincore"
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

    def test_get_dublincore_none_found(self):
        """It should not create a Dublin Core element if no info found."""
        sipuuid = "dnednedn-5bd2-4249-84a1-2f00f725b981"

        dc_elem = create_mets_v2.getDublinCore(self.siptypeuuid, sipuuid)
        assert dc_elem is None

    def test_create_dc_dmdsec_dc_exists(self):
        """It should create a dmdSec if DC information exists."""
        # Generate dmdSec if DC exists
        state = create_mets_v2.MetsState()
        dmdsec_elem, dmdid = create_mets_v2.createDublincoreDMDSecFromDBData(
            Job("stub", "stub", []), self.siptypeuuid, self.sipuuid, THIS_DIR, state
        )
        # Verify created correctly
        assert dmdsec_elem is not None
        assert dmdsec_elem.tag == "{http://www.loc.gov/METS/}dmdSec"
        assert dmdsec_elem.attrib["ID"] == dmdid
        assert len(dmdsec_elem) == 1
        mdwrap = dmdsec_elem[0]
        assert mdwrap.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert mdwrap.attrib["MDTYPE"] == "DC"
        assert len(mdwrap) == 1
        xmldata = mdwrap[0]
        assert xmldata.tag == "{http://www.loc.gov/METS/}xmlData"
        assert len(xmldata) == 1
        assert xmldata[0].tag == "{http://purl.org/dc/terms/}dublincore"

    def test_create_dc_dmdsec_no_dc_no_transfers_dir(self):
        """It should not fail if no transfers directory exists."""
        badsipuuid = "dnednedn-5bd2-4249-84a1-2f00f725b981"
        state = create_mets_v2.MetsState()
        dmdsec_elem = create_mets_v2.createDublincoreDMDSecFromDBData(
            Job("stub", "stub", []), self.siptypeuuid, badsipuuid, THIS_DIR, state
        )
        # Expect no element
        assert dmdsec_elem is None

    def test_create_dc_dmdsec_no_dc_no_transfers(self):
        """It should not fail if no dublincore.xml exists from transfers."""
        badsipuuid = "dnednedn-5bd2-4249-84a1-2f00f725b981"
        sip_dir = Path(tempfile.mkdtemp()) / "emptysip"
        try:
            shutil.copytree(
                os.path.join(THIS_DIR, "fixtures", "emptysip"), str(sip_dir)
            )
            # Make sure directory is empty
            (sip_dir / "objects/metadata/transfers/.gitignore").unlink()
            state = create_mets_v2.MetsState()
            dmdsec_elem = create_mets_v2.createDublincoreDMDSecFromDBData(
                Job("stub", "stub", []),
                self.siptypeuuid,
                badsipuuid,
                str(sip_dir),
                state,
            )
            assert dmdsec_elem is None
        finally:
            shutil.rmtree(str(sip_dir.parent))

    @unittest.expectedFailure
    def test_create_dc_dmdsec_no_dc_transfer_dc_xml(self):
        # FIXME What is the expected behaviour of this? What should the fixture have?
        # transfers_sip = os.path.join(THIS_DIR, 'fixtures', 'transfer_dc')
        raise NotImplementedError()

    def test_dmdsec_from_csv_parsed_metadata_dc_only(self):
        """It should only create a DC dmdSec from parsed metadata."""
        data = collections.OrderedDict(
            [
                ("dc.title", ["Yamani Weapons"]),
                ("dc.creator", ["Keladry of Mindelan"]),
                ("dc.subject", ["Glaives"]),
                ("dc.description", ["Glaives are cool"]),
                ("dc.publisher", ["Tortall Press"]),
                ("dc.contributor", ["雪 ユキ".encode("utf8")]),
                ("dc.date", ["2015"]),
                ("dc.type", ["Archival Information Package"]),
                ("dc.format", ["parchement"]),
                ("dc.identifier", ["42/1"]),
                ("dc.source", ["Numair's library"]),
                ("dc.relation", ["None"]),
                ("dc.language", ["en"]),
                ("dc.rights", ["Public Domain"]),
                ("dcterms.isPartOf", ["AIC#42"]),
            ]
        )
        # Test
        state = create_mets_v2.MetsState()
        ret = create_mets_v2.createDmdSecsFromCSVParsedMetadata(
            Job("stub", "stub", []), data, state
        )
        # Verify
        assert ret
        assert len(ret) == 1
        dmdsec = ret[0]
        assert dmdsec.tag == "{http://www.loc.gov/METS/}dmdSec"
        assert "ID" in dmdsec.attrib
        mdwrap = dmdsec[0]
        assert mdwrap.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert "MDTYPE" in mdwrap.attrib
        assert mdwrap.attrib["MDTYPE"] == "DC"
        xmldata = mdwrap[0]
        assert xmldata.tag == "{http://www.loc.gov/METS/}xmlData"
        # Elements are children of dublincore tag
        dc_elem = xmldata[0]
        assert dc_elem.tag == "{http://purl.org/dc/terms/}dublincore"
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
        assert dc_elem[5].text == "雪 ユキ"
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

    def test_dmdsec_from_csv_parsed_metadata_other_only(self):
        """It should only create an Other dmdSec from parsed metadata."""
        data = collections.OrderedDict(
            [
                ("Title", ["Yamani Weapons"]),
                ("Contributor", ["雪 ユキ".encode("utf8")]),
                (
                    "Long Description",
                    ["This is about how glaives are used in the Yamani Islands"],
                ),
            ]
        )
        # Test
        state = create_mets_v2.MetsState()
        ret = create_mets_v2.createDmdSecsFromCSVParsedMetadata(
            Job("stub", "stub", []), data, state
        )
        # Verify
        assert ret
        assert len(ret) == 1
        dmdsec = ret[0]
        assert dmdsec.tag == "{http://www.loc.gov/METS/}dmdSec"
        assert "ID" in dmdsec.attrib
        mdwrap = dmdsec[0]
        assert mdwrap.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert "MDTYPE" in mdwrap.attrib
        assert mdwrap.attrib["MDTYPE"] == "OTHER"
        assert "OTHERMDTYPE" in mdwrap.attrib
        assert mdwrap.attrib["OTHERMDTYPE"] == "CUSTOM"
        xmldata = mdwrap[0]
        assert xmldata.tag == "{http://www.loc.gov/METS/}xmlData"
        # Elements are direct children of xmlData
        assert len(xmldata) == 3
        assert xmldata[0].tag == "title"
        assert xmldata[0].text == "Yamani Weapons"
        assert xmldata[1].tag == "contributor"
        assert xmldata[1].text == "雪 ユキ"
        assert xmldata[2].tag == "long_description"
        assert (
            xmldata[2].text
            == "This is about how glaives are used in the Yamani Islands"
        )

    def test_dmdsec_from_csv_parsed_metadata_both(self):
        """It should create a dmdSec for DC and Other parsed metadata."""
        data = collections.OrderedDict(
            [
                ("dc.title", ["Yamani Weapons"]),
                ("dc.contributor", ["雪 ユキ".encode("utf8")]),
                ("dcterms.isPartOf", ["AIC#42"]),
                ("Title", ["Yamani Weapons"]),
                ("Contributor", ["雪 ユキ".encode("utf8")]),
                (
                    "Long Description",
                    ["This is about how glaives are used in the Yamani Islands"],
                ),
            ]
        )
        # Test
        state = create_mets_v2.MetsState()
        ret = create_mets_v2.createDmdSecsFromCSVParsedMetadata(
            Job("stub", "stub", []), data, state
        )
        # Verify
        assert ret
        assert len(ret) == 2
        # Return can be DC or OTHER first, but in this case DC should be first
        dc_dmdsec = ret[0]
        assert dc_dmdsec.tag == "{http://www.loc.gov/METS/}dmdSec"
        assert "ID" in dc_dmdsec.attrib
        mdwrap = dc_dmdsec[0]
        assert mdwrap.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert "MDTYPE" in mdwrap.attrib
        assert mdwrap.attrib["MDTYPE"] == "DC"
        xmldata = mdwrap[0]
        assert xmldata.tag == "{http://www.loc.gov/METS/}xmlData"
        dc_elem = xmldata[0]
        # Elements are children of dublincore tag
        assert dc_elem.tag == "{http://purl.org/dc/terms/}dublincore"
        assert len(dc_elem) == 3
        assert dc_elem[0].tag == "{http://purl.org/dc/elements/1.1/}title"
        assert dc_elem[0].text == "Yamani Weapons"
        assert dc_elem[1].tag == "{http://purl.org/dc/elements/1.1/}contributor"
        assert dc_elem[1].text == "雪 ユキ"
        assert dc_elem[2].tag == "{http://purl.org/dc/terms/}isPartOf"
        assert dc_elem[2].text == "AIC#42"

        other_dmdsec = ret[1]
        assert other_dmdsec.tag == "{http://www.loc.gov/METS/}dmdSec"
        assert "ID" in other_dmdsec.attrib
        mdwrap = other_dmdsec[0]
        assert mdwrap.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert "MDTYPE" in mdwrap.attrib
        assert mdwrap.attrib["MDTYPE"] == "OTHER"
        assert "OTHERMDTYPE" in mdwrap.attrib
        assert mdwrap.attrib["OTHERMDTYPE"] == "CUSTOM"
        xmldata = mdwrap[0]
        assert xmldata.tag == "{http://www.loc.gov/METS/}xmlData"
        # Elements are direct children of xmlData
        assert len(xmldata) == 3
        assert xmldata[0].tag == "title"
        assert xmldata[0].text == "Yamani Weapons"
        assert xmldata[1].tag == "contributor"
        assert xmldata[1].text == "雪 ユキ"
        assert xmldata[2].tag == "long_description"
        assert (
            xmldata[2].text
            == "This is about how glaives are used in the Yamani Islands"
        )

    def test_dmdsec_from_csv_parsed_metadata_no_data(self):
        """It should not create dmdSecs with no parsed metadata."""
        data = {}
        # Test
        state = create_mets_v2.MetsState()
        ret = create_mets_v2.createDmdSecsFromCSVParsedMetadata(
            Job("stub", "stub", []), data, state
        )
        # Verify
        assert ret == []

    def test_dmdsec_from_csv_parsed_metadata_repeats(self):
        """It should create multiple elements for repeated input."""
        data = collections.OrderedDict(
            [
                ("dc.contributor", ["Yuki", "雪 ユキ".encode("utf8")]),
                ("Contributor", ["Yuki", "雪 ユキ".encode("utf8")]),
            ]
        )
        # Test
        state = create_mets_v2.MetsState()
        ret = create_mets_v2.createDmdSecsFromCSVParsedMetadata(
            Job("stub", "stub", []), data, state
        )
        # Verify
        assert ret
        assert len(ret) == 2
        # Return can be DC or OTHER first, but in this case DC should be first
        dc_dmdsec = ret[0]
        assert dc_dmdsec.tag == "{http://www.loc.gov/METS/}dmdSec"
        assert "ID" in dc_dmdsec.attrib
        mdwrap = dc_dmdsec[0]
        assert mdwrap.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert "MDTYPE" in mdwrap.attrib
        assert mdwrap.attrib["MDTYPE"] == "DC"
        xmldata = mdwrap[0]
        assert xmldata.tag == "{http://www.loc.gov/METS/}xmlData"
        dc_elem = xmldata[0]
        # Elements are children of dublincore tag
        assert dc_elem.tag == "{http://purl.org/dc/terms/}dublincore"
        assert len(dc_elem) == 2
        assert dc_elem[0].tag == "{http://purl.org/dc/elements/1.1/}contributor"
        assert dc_elem[0].text == "Yuki"
        assert dc_elem[1].tag == "{http://purl.org/dc/elements/1.1/}contributor"
        assert dc_elem[1].text == "雪 ユキ"

        other_dmdsec = ret[1]
        assert other_dmdsec.tag == "{http://www.loc.gov/METS/}dmdSec"
        assert "ID" in other_dmdsec.attrib
        mdwrap = other_dmdsec[0]
        assert mdwrap.tag == "{http://www.loc.gov/METS/}mdWrap"
        assert "MDTYPE" in mdwrap.attrib
        assert mdwrap.attrib["MDTYPE"] == "OTHER"
        assert "OTHERMDTYPE" in mdwrap.attrib
        assert mdwrap.attrib["OTHERMDTYPE"] == "CUSTOM"
        xmldata = mdwrap[0]
        assert xmldata.tag == "{http://www.loc.gov/METS/}xmlData"
        # Elements are direct children of xmlData
        assert len(xmldata) == 2
        assert xmldata[0].tag == "contributor"
        assert xmldata[0].text == "Yuki"
        assert xmldata[1].tag == "contributor"
        assert xmldata[1].text == "雪 ユキ"


class TestCSVMetadata(TempDirMixin, TestCase):
    """Test parsing the metadata.csv."""

    def setUp(self):
        super(TestCSVMetadata, self).setUp()
        self.metadata_file = self.tmpdir / "metadata.csv"

    def test_parse_metadata_csv(self):
        """It should parse the metadata.csv into a dict."""
        # Create metadata.csv
        data = [
            ["Filename", "dc.title", "dc.date", "Other metadata"],
            ["objects/foo.jpg", "Foo", "2000", "Taken on a sunny day"],
            ["objects/bar/", "Bar", "2000", "All taken on a rainy day"],
        ]
        with open(self.metadata_file.as_posix(), "w") as f:
            writer = csv.writer(f)
            for row in data:
                writer.writerow(row)

        # Run test
        dc = archivematicaCreateMETSMetadataCSV.parseMetadataCSV(
            Job("stub", "stub", []), str(self.metadata_file)
        )
        # Verify
        assert dc
        assert "objects/foo.jpg" in dc
        assert "dc.title" in dc["objects/foo.jpg"]
        assert dc["objects/foo.jpg"]["dc.title"] == ["Foo"]
        assert "dc.date" in dc["objects/foo.jpg"]
        assert dc["objects/foo.jpg"]["dc.date"] == ["2000"]
        assert "Other metadata" in dc["objects/foo.jpg"]
        assert dc["objects/foo.jpg"]["Other metadata"] == ["Taken on a sunny day"]
        assert list(dc["objects/foo.jpg"].keys()) == [
            "dc.title",
            "dc.date",
            "Other metadata",
        ]

        assert "objects/bar" in dc
        assert "dc.title" in dc["objects/bar"]
        assert dc["objects/bar"]["dc.title"] == ["Bar"]
        assert "dc.date" in dc["objects/bar"]
        assert dc["objects/bar"]["dc.date"] == ["2000"]
        assert "Other metadata" in dc["objects/bar"]
        assert dc["objects/bar"]["Other metadata"] == ["All taken on a rainy day"]
        assert list(dc["objects/bar"].keys()) == [
            "dc.title",
            "dc.date",
            "Other metadata",
        ]

    def test_parse_metadata_csv_repeated_columns(self):
        """It should put repeated elements into a list of values."""
        # Create metadata.csv
        data = [
            ["Filename", "dc.title", "dc.type", "dc.type", "dc.type"],
            ["objects/foo.jpg", "Foo", "Photograph", "Still image", "Picture"],
        ]
        with open(self.metadata_file.as_posix(), "w") as f:
            writer = csv.writer(f)
            for row in data:
                writer.writerow(row)

        # Run test
        dc = archivematicaCreateMETSMetadataCSV.parseMetadataCSV(
            Job("stub", "stub", []), str(self.metadata_file)
        )
        # Verify
        assert dc
        assert "objects/foo.jpg" in dc
        assert "dc.title" in dc["objects/foo.jpg"]
        assert dc["objects/foo.jpg"]["dc.title"] == ["Foo"]
        assert "dc.type" in dc["objects/foo.jpg"]
        assert dc["objects/foo.jpg"]["dc.type"] == [
            "Photograph",
            "Still image",
            "Picture",
        ]
        assert list(dc["objects/foo.jpg"].keys()) == ["dc.title", "dc.type"]

    def test_parse_metadata_csv_non_ascii(self):
        """It should parse unicode."""
        # Create metadata.csv
        data = [["Filename", "dc.title"], ["objects/foo.jpg", six.ensure_str("元気です")]]
        with open(self.metadata_file.as_posix(), "w") as f:
            writer = csv.writer(f)
            for row in data:
                writer.writerow(row)

        # Run test
        dc = archivematicaCreateMETSMetadataCSV.parseMetadataCSV(
            Job("stub", "stub", []), str(self.metadata_file)
        )
        # Verify
        assert dc
        assert "objects/foo.jpg" in dc
        assert "dc.title" in dc["objects/foo.jpg"]
        assert dc["objects/foo.jpg"]["dc.title"] == [six.ensure_str("元気です")]

    def test_parse_metadata_csv_blank_rows(self):
        """It should skip blank rows."""
        # Create metadata.csv
        data = [
            ["Filename", "dc.title", "dc.type", "dc.type", "dc.type"],
            ["objects/foo.jpg", "Foo", "Photograph", "Still image", "Picture"],
            [],
        ]
        with open(self.metadata_file.as_posix(), "w") as f:
            writer = csv.writer(f)
            for row in data:
                writer.writerow(row)

        # Run test
        dc = archivematicaCreateMETSMetadataCSV.parseMetadataCSV(
            Job("stub", "stub", []), str(self.metadata_file)
        )
        # Verify
        assert dc
        assert len(dc) == 1
        assert "objects/foo.jpg" in dc


class TestCreateDigiprovMD(TestCase):
    """ Test creating PREMIS:EVENTS and PREMIS:AGENTS """

    fixture_files = [
        "metadata_applies_to_type.json",
        "agents.json",
        "sip.json",
        "files.json",
        "events-transfer.json",
    ]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def test_creates_events(self):
        """
        It should create Events
        It should create Agents
        It should link Events only with Agents for that Event
        It should only include Agents used by that file
        """
        state = create_mets_v2.MetsState()
        ret = create_mets_v2.createDigiprovMD(
            "ae8d4290-fe52-4954-b72a-0f591bee2e2f", state
        )
        assert len(ret) == 9
        # Events
        assert ret[0][0].attrib["MDTYPE"] == "PREMIS:EVENT"
        assert (
            ret[0].find(".//{http://www.loc.gov/premis/v3}eventType").text
            == "ingestion"
        )
        assert (
            len(
                ret[0].findall(
                    ".//{http://www.loc.gov/premis/v3}linkingAgentIdentifier"
                )
            )
            == 3
        )
        assert ret[1][0].attrib["MDTYPE"] == "PREMIS:EVENT"
        assert (
            ret[1].find(".//{http://www.loc.gov/premis/v3}eventType").text
            == "message digest calculation"
        )
        assert (
            len(
                ret[1].findall(
                    ".//{http://www.loc.gov/premis/v3}linkingAgentIdentifier"
                )
            )
            == 3
        )
        assert ret[2][0].attrib["MDTYPE"] == "PREMIS:EVENT"
        assert (
            ret[2].find(".//{http://www.loc.gov/premis/v3}eventType").text
            == "virus check"
        )
        assert (
            len(
                ret[2].findall(
                    ".//{http://www.loc.gov/premis/v3}linkingAgentIdentifier"
                )
            )
            == 3
        )
        assert ret[3][0].attrib["MDTYPE"] == "PREMIS:EVENT"
        assert (
            ret[3].find(".//{http://www.loc.gov/premis/v3}eventType").text
            == "filename change"
        )
        assert (
            len(
                ret[3].findall(
                    ".//{http://www.loc.gov/premis/v3}linkingAgentIdentifier"
                )
            )
            == 3
        )
        assert ret[4][0].attrib["MDTYPE"] == "PREMIS:EVENT"
        assert (
            ret[4].find(".//{http://www.loc.gov/premis/v3}eventType").text
            == "format identification"
        )
        assert (
            len(
                ret[4].findall(
                    ".//{http://www.loc.gov/premis/v3}linkingAgentIdentifier"
                )
            )
            == 3
        )
        assert ret[5][0].attrib["MDTYPE"] == "PREMIS:EVENT"
        assert (
            ret[5].find(".//{http://www.loc.gov/premis/v3}eventType").text
            == "validation"
        )
        assert (
            len(
                ret[5].findall(
                    ".//{http://www.loc.gov/premis/v3}linkingAgentIdentifier"
                )
            )
            == 3
        )
        # Agents
        assert ret[6][0].attrib["MDTYPE"] == "PREMIS:AGENT"
        assert (
            ret[6].find(".//{http://www.loc.gov/premis/v3}agentIdentifierType").text
            == "preservation system"
        )
        assert (
            ret[6].find(".//{http://www.loc.gov/premis/v3}agentIdentifierValue").text
            == get_preservation_system_identifier()
        )
        assert (
            ret[6].find(".//{http://www.loc.gov/premis/v3}agentName").text
            == "Archivematica"
        )
        assert (
            ret[6].find(".//{http://www.loc.gov/premis/v3}agentType").text == "software"
        )
        assert ret[7][0].attrib["MDTYPE"] == "PREMIS:AGENT"
        assert (
            ret[7].find(".//{http://www.loc.gov/premis/v3}agentIdentifierType").text
            == "repository code"
        )
        assert (
            ret[7].find(".//{http://www.loc.gov/premis/v3}agentIdentifierValue").text
            == "demo"
        )
        assert ret[7].find(".//{http://www.loc.gov/premis/v3}agentName").text == "demo"
        assert (
            ret[7].find(".//{http://www.loc.gov/premis/v3}agentType").text
            == "organization"
        )
        assert ret[8][0].attrib["MDTYPE"] == "PREMIS:AGENT"
        assert (
            ret[8].find(".//{http://www.loc.gov/premis/v3}agentIdentifierType").text
            == "Archivematica user pk"
        )
        assert (
            ret[8].find(".//{http://www.loc.gov/premis/v3}agentIdentifierValue").text
            == "1"
        )
        assert (
            ret[8].find(".//{http://www.loc.gov/premis/v3}agentName").text
            == 'username="kmindelan", first_name="Keladry", last_name="Mindelan"'
        )
        assert (
            ret[8].find(".//{http://www.loc.gov/premis/v3}agentType").text
            == "Archivematica user"
        )


class TestRights(TestCase):
    """ Test archivematicaCreateMETSRights creating rightsMD. """

    fixture_files = ["rights.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def test_create_rights_granted(self):
        # Setup
        elem = etree.Element(
            "{http://www.loc.gov/premis/v3}rightsStatement",
            nsmap={"premis": NSMAP["premis"]},
        )
        statement = RightsStatement.objects.get(id=1)
        # Test
        state = create_mets_v2.MetsState()
        archivematicaCreateMETSRights.getrightsGranted(
            Job("stub", "stub", []), statement, elem, state
        )
        # Verify
        assert len(elem) == 1
        rightsgranted = elem[0]
        assert rightsgranted.tag == "{http://www.loc.gov/premis/v3}rightsGranted"
        assert len(rightsgranted.attrib) == 0
        assert len(rightsgranted) == 4
        assert rightsgranted[0].tag == "{http://www.loc.gov/premis/v3}act"
        assert rightsgranted[0].text == "Disseminate"
        assert len(rightsgranted[0].attrib) == 0
        assert len(rightsgranted[0]) == 0
        assert rightsgranted[1].tag == "{http://www.loc.gov/premis/v3}restriction"
        assert rightsgranted[1].text == "Allow"
        assert len(rightsgranted[1].attrib) == 0
        assert len(rightsgranted[1]) == 0
        assert rightsgranted[2].tag == "{http://www.loc.gov/premis/v3}termOfGrant"
        assert len(rightsgranted[2].attrib) == 0
        assert len(rightsgranted[2]) == 2
        assert rightsgranted[2][0].tag == "{http://www.loc.gov/premis/v3}startDate"
        assert rightsgranted[2][0].text == "2000"
        assert rightsgranted[2][1].tag == "{http://www.loc.gov/premis/v3}endDate"
        assert rightsgranted[2][1].text == "OPEN"
        assert rightsgranted[3].tag == "{http://www.loc.gov/premis/v3}rightsGrantedNote"
        assert rightsgranted[3].text == "Attribution required"
        assert len(rightsgranted[3].attrib) == 0
        assert len(rightsgranted[3]) == 0


class TestCustomStructMap(TempDirMixin, TestCase):
    """Test creation of custom structMap."""

    fixture_files = [
        os.path.join("custom_structmaps", "model", "sip.json"),
        os.path.join("custom_structmaps", "model", "files.json"),
    ]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]
    mets_xsd_path = os.path.abspath(
        os.path.join(THIS_DIR, "../lib/assets/mets/mets.xsd")
    )

    @staticmethod
    def count_dir_objects(path):
        """Count all objects on a given path tree."""
        return sum([len(files) for _, dir_, files in scandir.walk(path)])

    @staticmethod
    def validate_mets(mets_xsd, mets_structmap):
        """Validate the provided mets structmap."""
        xmlschema = etree.XMLSchema(etree.parse(mets_xsd))
        try:
            xmlschema.assertValid(etree.parse(mets_structmap))
        except TypeError:
            rootName = etree.QName(ns.metsNS, "mets")
            root = etree.Element(rootName, nsmap={"mets": ns.metsNS})
            root.append(mets_structmap)
            xmlschema.assertValid(
                etree.fromstring(
                    etree.tostring(root, encoding="utf-8", xml_declaration=True)
                )
            )

    def _fixup_fileid_state(self):
        """For items on-disk we have to mimic the filename change process."""
        for key, _ in dict(self.state.fileNameToFileID).items():
            self.state.fileNameToFileID[
                create_mets_v2._fixup_path_input_by_user(Job("stub", "stub", []), key)
            ] = self.state.fileNameToFileID.pop(key)

    def generate_aip_mets_v2_state(self):
        """Generate fileSec state

        State will be generated that we will help us to test the units involved
        with creating a custom structmap in the AIP METS.
        """
        arbitrary_max_structmaps = 10
        self.transfer_dir = os.path.join(
            THIS_DIR,
            "fixtures",
            "custom_structmaps",
            "custom-structmap-3a915449-d1bb-4920-b274-c917c7bb5929",
            "",
        )
        self.objects_dir = os.path.join(self.transfer_dir, "objects")
        structMap = etree.Element(
            ns.metsBNS + "structMap",
            TYPE="physical",
            ID="structMap_1",
            LABEL="Archivematica default",
        )
        # Input to create_file_sec:
        #
        # <ns0:div xmlns:ns0="http://www.loc.gov/METS/"
        #          LABEL="3-031927e0-63bb-430c-8b37-fc799c132ca9"
        #          TYPE="Directory"
        #          DMDID="dmdSec_1"
        # />
        #
        sip_dir_name = os.path.basename(self.objects_dir.rstrip(os.path.sep))
        structMapDiv = etree.SubElement(
            structMap, ns.metsBNS + "div", TYPE="Directory", LABEL=sip_dir_name
        )
        self.state = create_mets_v2.MetsState()
        self.state.globalStructMapCounter = random.choice(
            [x for x in range(arbitrary_max_structmaps)]
        )
        self.structmap_div_element = create_mets_v2.createFileSec(
            job=Job("stub", "stub", []),
            directoryPath=self.objects_dir,
            parentDiv=structMapDiv,
            baseDirectoryPath=self.transfer_dir,
            sipUUID="3a915449-d1bb-4920-b274-c917c7bb5929",
            directories={},
            state=self.state,
            includeAmdSec=True,
        )

    def test_create_file_sec(self):
        """Test the output of a generating a fileSec

        As we rely on the state created by generating a fileSec we might as
        well do some additional testing along the way to ensure that what is
        created aligns with what we're expecting and remains that.
        """
        self.generate_aip_mets_v2_state()
        # Example output from createFileSec(...) to generate
        # self.structmap_div_element.
        #
        # <ns0:div xmlns:ns0="http://www.loc.gov/METS/" LABEL="objects" TYPE="Directory">
        #   <ns0:div LABEL="test_file.flac" TYPE="Item">
        #       <ns0:fptr FILEID="file-e334a1d6-a068-4bf2-9f89-839af1a26763"/>
        #   </ns0:div>
        # </ns0:div>
        #
        labels = self.structmap_div_element.xpath(
            '//mets:div[@TYPE="Item"]', namespaces=ns.NSMAP
        )
        fptrs = self.structmap_div_element.xpath(
            "//mets:fptr[@FILEID]", namespaces=ns.NSMAP
        )
        fnames = [label.attrib["LABEL"] for label in labels]
        uuids = [fptr.attrib["FILEID"] for fptr in fptrs]
        assert isinstance(
            self.structmap_div_element, etree._Element
        ), "createFileSec didn't return an XML structure to work with"
        assert self.count_dir_objects(self.objects_dir) == (
            len(fnames) and len(uuids)
        ), "Count of objects on disk and in fileSec do not match."
        assert (
            self.state.fileNameToFileID is not None
        ), "fileNameToFileID mapping hasn't been generated"
        assert self.count_dir_objects(self.objects_dir) == len(
            self.state.fileNameToFileID
        ), "State hasn't been generated for all objects on disk, duplicate names may not be counted for"

    def test_get_included_structmap_invalid_mets(self):
        """Integration test ensuring that it is possible for the mets
        validation to fail using the mets_xsd_path included with Archivematica.
        """
        self.generate_aip_mets_v2_state()
        broken_structmap_path = os.path.join(
            self.objects_dir,
            "metadata",
            "transfers",
            "custom-structmap-41ab1f1a-34d0-4a83-a2a3-0ad1b1ee1c51",
            "broken_structmap.xml",
        )
        assert os.path.isfile(broken_structmap_path)
        assert os.path.isfile(self.mets_xsd_path)
        try:
            self.validate_mets(self.mets_xsd_path, broken_structmap_path)
        except etree.DocumentInvalid:
            assert (
                True
            ), "Expecting a validation error so that we know validation is working correctly"

    def test_get_included_structmap_valid_mets(self):
        """Test the valid output of custom structmaps in create_mets_v2."""
        self.generate_aip_mets_v2_state()
        self._fixup_fileid_state()
        default_structmap = "mets_structmap.xml"
        Result = collections.namedtuple(
            "Result", "structmap_name files replaced_count structmap_id"
        )
        results = [
            Result(None, ["objects/test_file.flac"], 1, None),
            Result(
                "simple_book_structmap.xml",
                ["objects/test_file.jpg", "objects/test_file.png"],
                2,
                None,
            ),
            Result("mets_area_structmap.xml", ["test_file.mp3"], 6, None),
            Result(
                "unicode_simple_book_structmap.xml",
                ["objects/página_de_prueba.jpg", "objects/página_de_prueba.png"],
                2,
                "custom_structmap",
            ),
            Result(
                "nested_file_structmap.xml",
                ["objects/nested_dir/nested_file.rdata"],
                6,
                None,
            ),
            Result(
                "complex_book_structmap.xml",
                [
                    "objects/nested_dir/duplicate_file_name.png",
                    "objects/duplicate_file_name.png",
                ],
                2,
                None,
            ),
            Result(
                "path_with_spaces_structmap.xml",
                ["objects/dir-with-dashes/file with spaces.bin"],
                1,
                None,
            ),
        ]
        for res in results:
            structmap_path = os.path.join(
                self.objects_dir,
                "metadata",
                "transfers",
                "custom-structmap-41ab1f1a-34d0-4a83-a2a3-0ad1b1ee1c51",
                (default_structmap if not res.structmap_name else res.structmap_name),
            )
            assert os.path.isfile(structmap_path)
            assert os.path.isfile(self.mets_xsd_path)
            self.validate_mets(self.mets_xsd_path, structmap_path)
            # Ensure that we test default behavior.
            if not res.structmap_name:
                custom_structmap = create_mets_v2.include_custom_structmap(
                    job=Job("stub", "stub", []),
                    baseDirectoryPath=self.transfer_dir,
                    state=self.state,
                )[0]
            else:
                # Expand the scope of testing to all our sample structmaps.
                custom_structmap = create_mets_v2.include_custom_structmap(
                    job=Job("stub", "stub", []),
                    baseDirectoryPath=self.transfer_dir,
                    state=self.state,
                    custom_structmap=res.structmap_name,
                )[0]
            # All custom structmaps that are used and return from this function
            # should remain valid.
            self.validate_mets(self.mets_xsd_path, custom_structmap)
            assert custom_structmap.tag == "{{{}}}structMap".format(ns.metsNS)
            if not res.structmap_id:
                assert custom_structmap.attrib["ID"].lower() == "structmap_{}".format(
                    self.state.globalStructMapCounter
                ), "structmap id is incorrect"
            else:
                assert (
                    custom_structmap.attrib["ID"].lower() == res.structmap_id
                ), "structmap id hasn't been maintained"
            fids = custom_structmap.xpath(
                "//*[@FILEID]", namespaces={"mets:": ns.metsNS}
            )
            assert len(fids) == res.replaced_count, "Count of FILEIDs is incorrect"
            assert len(set([fid.attrib["FILEID"] for fid in fids])) == len(
                res.files
            ), "Uneven replacement of IDs for files in structmap"
            for fileid in [fid.attrib["FILEID"] for fid in fids]:
                assert fileid in list(
                    self.state.fileNameToFileID.values()
                ), "Expected FILEID not in returned structmap"

    def test_get_included_structmap_incomplete_mets(self):
        """Test the output of custom structmaps in create_mets_v2 where the
        structMap is incomplete.
        """
        self.generate_aip_mets_v2_state()
        self._fixup_fileid_state()
        default_structmap = "mets_structmap.xml"
        Result = collections.namedtuple("Result", "structmap_name structmap_id")
        results = [
            Result("no-contentids.xml", "custom_structmap"),
            Result("file_does_not_exist.xml", "custom_structmap"),
            Result("empty_filenames.xml", "custom_structmap"),
            Result("missing_contentid.xml", "custom_structmap"),
        ]
        for res in results:
            self.state = create_mets_v2.MetsState()
            structmap_path = os.path.join(
                self.objects_dir,
                "metadata",
                "transfers",
                "custom-structmap-41ab1f1a-34d0-4a83-a2a3-0ad1b1ee1c51",
                (default_structmap if not res.structmap_name else res.structmap_name),
            )
            assert os.path.isfile(structmap_path)
            assert os.path.isfile(self.mets_xsd_path)
            self.validate_mets(self.mets_xsd_path, structmap_path)
            custom_structmap = create_mets_v2.include_custom_structmap(
                job=Job("stub", "stub", []),
                baseDirectoryPath=self.transfer_dir,
                state=self.state,
                custom_structmap=res.structmap_name,
            )
            assert (
                custom_structmap == []
            ), "Return from include_custom_structmap should be an empty array: {}".format(
                custom_structmap
            )
            assert (
                self.state.error_accumulator.error_count == 1
            ), "error counter should be incremented on error"
