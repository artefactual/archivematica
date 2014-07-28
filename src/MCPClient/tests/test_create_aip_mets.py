# -*- coding: utf8
import collections
import csv
import os
import sys

from django.test import TestCase

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))
import archivematicaCreateMETS2
import archivematicaCreateMETSMetadataCSV

from main.models import DublinCore

class TestDublinCore(TestCase):

    fixture_files = ['dublincore.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]
    sipuuid = '8b891d7c-5bd2-4249-84a1-2f00f725b981'
    siptypeuuid = '3e48343d-e2d2-4956-aaa3-b54d26eb9761'

    def test_get_dublincore(self):

        # Generate DC element from DB
        dc_elem = archivematicaCreateMETS2.getDublinCore(self.siptypeuuid, self.sipuuid)

        # Verify created correctly
        assert dc_elem is not None
        assert dc_elem.tag == '{http://purl.org/dc/terms/}dublincore'
        assert len(dc_elem) == 15
        assert dc_elem[0].tag == '{http://purl.org/dc/elements/1.1/}title'
        assert dc_elem[0].text == 'Yamani Weapons'
        assert dc_elem[1].tag == '{http://purl.org/dc/elements/1.1/}creator'
        assert dc_elem[1].text == 'Keladry of Mindelan'
        assert dc_elem[2].tag == '{http://purl.org/dc/elements/1.1/}subject'
        assert dc_elem[2].text == 'Glaives'
        assert dc_elem[3].tag == '{http://purl.org/dc/elements/1.1/}description'
        assert dc_elem[3].text == 'Glaives are cool'
        assert dc_elem[4].tag == '{http://purl.org/dc/elements/1.1/}publisher'
        assert dc_elem[4].text == 'Tortall Press'
        assert dc_elem[5].tag == '{http://purl.org/dc/elements/1.1/}contributor'
        assert dc_elem[5].text == 'Yuki'
        assert dc_elem[6].tag == '{http://purl.org/dc/elements/1.1/}date'
        assert dc_elem[6].text == '2015'
        assert dc_elem[7].tag == '{http://purl.org/dc/elements/1.1/}type'
        assert dc_elem[7].text == 'Archival Information Package'
        assert dc_elem[8].tag == '{http://purl.org/dc/elements/1.1/}format'
        assert dc_elem[8].text == 'parchement'
        assert dc_elem[9].tag == '{http://purl.org/dc/elements/1.1/}identifier'
        assert dc_elem[9].text == '42/1'
        assert dc_elem[10].tag == '{http://purl.org/dc/elements/1.1/}source'
        assert dc_elem[10].text == "Numair's library"
        assert dc_elem[11].tag == '{http://purl.org/dc/elements/1.1/}relation'
        assert dc_elem[11].text == 'None'
        assert dc_elem[12].tag == '{http://purl.org/dc/elements/1.1/}language'
        assert dc_elem[12].text == 'en'
        assert dc_elem[13].tag == '{http://purl.org/dc/elements/1.1/}rights'
        assert dc_elem[13].text == 'Public Domain'
        assert dc_elem[14].tag == '{http://purl.org/dc/terms/}isPartOf'
        assert dc_elem[14].text == 'AIC#42'

    def test_get_dublincore_none_found(self):
        sipuuid = 'dnednedn-5bd2-4249-84a1-2f00f725b981'

        dc_elem = archivematicaCreateMETS2.getDublinCore(self.siptypeuuid, sipuuid)
        assert dc_elem is None

    def test_create_dc_dmdsec_dc_exists(self):
        # Generate dmdSec if DC exists
        dmdsec_elem, dmdid = archivematicaCreateMETS2.createDublincoreDMDSecFromDBData(self.siptypeuuid, self.sipuuid, THIS_DIR)
        # Verify created correctly
        assert dmdsec_elem is not None
        assert dmdsec_elem.tag == '{http://www.loc.gov/METS/}dmdSec'
        assert dmdsec_elem.attrib['ID'] == dmdid
        assert len(dmdsec_elem) == 1
        mdwrap = dmdsec_elem[0]
        assert mdwrap.tag == '{http://www.loc.gov/METS/}mdWrap'
        assert mdwrap.attrib['MDTYPE'] == 'DC'
        assert len(mdwrap) == 1
        xmldata = mdwrap[0]
        assert xmldata.tag == '{http://www.loc.gov/METS/}xmlData'
        assert len(xmldata) == 1
        assert xmldata[0].tag == '{http://purl.org/dc/terms/}dublincore'

    def test_create_dc_dmdsec_no_dc_no_transfers_dir(self):
        badsipuuid = 'dnednedn-5bd2-4249-84a1-2f00f725b981'
        dmdsec_elem = archivematicaCreateMETS2.createDublincoreDMDSecFromDBData(self.siptypeuuid, badsipuuid, THIS_DIR)
        # Expect no element
        assert dmdsec_elem is None

    def test_create_dc_dmdsec_no_dc_no_transfers(self):
        badsipuuid = 'dnednedn-5bd2-4249-84a1-2f00f725b981'
        empty_transfers_sip = os.path.join(THIS_DIR, 'fixtures', 'emptysip')
        # Make sure directory is empty
        try:
            os.remove(os.path.join(empty_transfers_sip, 'objects', 'metadata', 'transfers', '.gitignore'))
        except OSError:
            pass
        dmdsec_elem = archivematicaCreateMETS2.createDublincoreDMDSecFromDBData(self.siptypeuuid, badsipuuid, empty_transfers_sip)
        assert dmdsec_elem is None
        # Reset directory state
        with open(os.path.join(empty_transfers_sip, 'objects', 'metadata', 'transfers', '.gitignore'), 'w'):
            pass

    def test_create_dc_dmdsec_no_dc_transfer_dc_xml(self):
        # FIXME What is the expected behaviour of this? What should the fixture have?
        transfers_sip = os.path.join(THIS_DIR, 'fixtures', 'transfer_dc')

    def test_dmdsec_from_csv_parsed_metadata_dc_only(self):
        data = collections.OrderedDict([
            ("dc.title", ["Yamani Weapons"]),
            ("dc.creator", ["Keladry of Mindelan"]),
            ("dc.subject", ["Glaives"]),
            ("dc.description", ["Glaives are cool"]),
            ("dc.publisher", ["Tortall Press"]),
            ("dc.contributor", [u"雪 ユキ".encode('utf8')]),
            ("dc.date", ["2015"]),
            ("dc.type", ["Archival Information Package"]),
            ("dc.format", ["parchement"]),
            ("dc.identifier", ["42/1"]),
            ("dc.source", ["Numair's library"]),
            ("dc.relation", ["None"]),
            ("dc.language", ["en"]),
            ("dc.rights", ["Public Domain"]),
            ("dcterms.isPartOf", ["AIC#42"]),
        ])
        # Test
        ret = archivematicaCreateMETS2.createDmdSecsFromCSVParsedMetadata(data)
        # Verify
        assert ret
        assert len(ret) == 1
        dmdsec = ret[0]
        assert dmdsec.tag == '{http://www.loc.gov/METS/}dmdSec'
        assert 'ID' in dmdsec.attrib
        mdwrap = dmdsec[0]
        assert mdwrap.tag == '{http://www.loc.gov/METS/}mdWrap'
        assert 'MDTYPE' in mdwrap.attrib
        assert mdwrap.attrib['MDTYPE'] == 'DC'
        xmldata = mdwrap[0]
        assert xmldata.tag == '{http://www.loc.gov/METS/}xmlData'
        # Elements are children of dublincore tag
        dc_elem = xmldata[0]
        assert dc_elem.tag == '{http://purl.org/dc/terms/}dublincore'
        assert len(dc_elem) == 15
        assert dc_elem[0].tag == '{http://purl.org/dc/elements/1.1/}title'
        assert dc_elem[0].text == 'Yamani Weapons'
        assert dc_elem[1].tag == '{http://purl.org/dc/elements/1.1/}creator'
        assert dc_elem[1].text == 'Keladry of Mindelan'
        assert dc_elem[2].tag == '{http://purl.org/dc/elements/1.1/}subject'
        assert dc_elem[2].text == 'Glaives'
        assert dc_elem[3].tag == '{http://purl.org/dc/elements/1.1/}description'
        assert dc_elem[3].text == 'Glaives are cool'
        assert dc_elem[4].tag == '{http://purl.org/dc/elements/1.1/}publisher'
        assert dc_elem[4].text == 'Tortall Press'
        assert dc_elem[5].tag == '{http://purl.org/dc/elements/1.1/}contributor'
        assert dc_elem[5].text == u'雪 ユキ'
        assert dc_elem[6].tag == '{http://purl.org/dc/elements/1.1/}date'
        assert dc_elem[6].text == '2015'
        assert dc_elem[7].tag == '{http://purl.org/dc/elements/1.1/}type'
        assert dc_elem[7].text == 'Archival Information Package'
        assert dc_elem[8].tag == '{http://purl.org/dc/elements/1.1/}format'
        assert dc_elem[8].text == 'parchement'
        assert dc_elem[9].tag == '{http://purl.org/dc/elements/1.1/}identifier'
        assert dc_elem[9].text == '42/1'
        assert dc_elem[10].tag == '{http://purl.org/dc/elements/1.1/}source'
        assert dc_elem[10].text == "Numair's library"
        assert dc_elem[11].tag == '{http://purl.org/dc/elements/1.1/}relation'
        assert dc_elem[11].text == 'None'
        assert dc_elem[12].tag == '{http://purl.org/dc/elements/1.1/}language'
        assert dc_elem[12].text == 'en'
        assert dc_elem[13].tag == '{http://purl.org/dc/elements/1.1/}rights'
        assert dc_elem[13].text == 'Public Domain'
        assert dc_elem[14].tag == '{http://purl.org/dc/terms/}isPartOf'
        assert dc_elem[14].text == 'AIC#42'

    def test_dmdsec_from_csv_parsed_metadata_other_only(self):
        data = collections.OrderedDict([
            ("Title", ["Yamani Weapons"]),
            ("Contributor", [u"雪 ユキ".encode('utf8')]),
            ("Long Description", ['This is about how glaives are used in the Yamani Islands'])
        ])
        # Test
        ret = archivematicaCreateMETS2.createDmdSecsFromCSVParsedMetadata(data)
        # Verify
        assert ret
        assert len(ret) == 1
        dmdsec = ret[0]
        assert dmdsec.tag == '{http://www.loc.gov/METS/}dmdSec'
        assert 'ID' in dmdsec.attrib
        mdwrap = dmdsec[0]
        assert mdwrap.tag == '{http://www.loc.gov/METS/}mdWrap'
        assert 'MDTYPE' in mdwrap.attrib
        assert mdwrap.attrib['MDTYPE'] == 'OTHER'
        assert 'OTHERMDTYPE' in mdwrap.attrib
        assert mdwrap.attrib['OTHERMDTYPE'] == 'CUSTOM'
        xmldata = mdwrap[0]
        assert xmldata.tag == '{http://www.loc.gov/METS/}xmlData'
        # Elements are direct children of xmlData
        assert len(xmldata) == 3
        assert xmldata[0].tag == 'title'
        assert xmldata[0].text == 'Yamani Weapons'
        assert xmldata[1].tag == 'contributor'
        assert xmldata[1].text == u'雪 ユキ'
        assert xmldata[2].tag == 'long_description'
        assert xmldata[2].text == 'This is about how glaives are used in the Yamani Islands'


    def test_dmdsec_from_csv_parsed_metadata_both(self):
        data = collections.OrderedDict([
            ("dc.title", ["Yamani Weapons"]),
            ("dc.contributor", [u"雪 ユキ".encode('utf8')]),
            ("dcterms.isPartOf", ["AIC#42"]),
            ("Title", ["Yamani Weapons"]),
            ("Contributor", [u"雪 ユキ".encode('utf8')]),
            ("Long Description", ['This is about how glaives are used in the Yamani Islands'])
        ])
        # Test
        ret = archivematicaCreateMETS2.createDmdSecsFromCSVParsedMetadata(data)
        # Verify
        assert ret
        assert len(ret) == 2
        # Return can be DC or OTHER first, but in this case DC should be first
        dc_dmdsec = ret[0]
        assert dc_dmdsec.tag == '{http://www.loc.gov/METS/}dmdSec'
        assert 'ID' in dc_dmdsec.attrib
        mdwrap = dc_dmdsec[0]
        assert mdwrap.tag == '{http://www.loc.gov/METS/}mdWrap'
        assert 'MDTYPE' in mdwrap.attrib
        assert mdwrap.attrib['MDTYPE'] == 'DC'
        xmldata = mdwrap[0]
        assert xmldata.tag == '{http://www.loc.gov/METS/}xmlData'
        dc_elem = xmldata[0]
        # Elements are children of dublincore tag
        assert dc_elem.tag == '{http://purl.org/dc/terms/}dublincore'
        assert len(dc_elem) == 3
        assert dc_elem[0].tag == '{http://purl.org/dc/elements/1.1/}title'
        assert dc_elem[0].text == 'Yamani Weapons'
        assert dc_elem[1].tag == '{http://purl.org/dc/elements/1.1/}contributor'
        assert dc_elem[1].text == u'雪 ユキ'
        assert dc_elem[2].tag == '{http://purl.org/dc/terms/}isPartOf'
        assert dc_elem[2].text == 'AIC#42'

        other_dmdsec = ret[1]
        assert other_dmdsec.tag == '{http://www.loc.gov/METS/}dmdSec'
        assert 'ID' in other_dmdsec.attrib
        mdwrap = other_dmdsec[0]
        assert mdwrap.tag == '{http://www.loc.gov/METS/}mdWrap'
        assert 'MDTYPE' in mdwrap.attrib
        assert mdwrap.attrib['MDTYPE'] == 'OTHER'
        assert 'OTHERMDTYPE' in mdwrap.attrib
        assert mdwrap.attrib['OTHERMDTYPE'] == 'CUSTOM'
        xmldata = mdwrap[0]
        assert xmldata.tag == '{http://www.loc.gov/METS/}xmlData'
        # Elements are direct children of xmlData
        assert len(xmldata) == 3
        assert xmldata[0].tag == 'title'
        assert xmldata[0].text == 'Yamani Weapons'
        assert xmldata[1].tag == 'contributor'
        assert xmldata[1].text == u'雪 ユキ'
        assert xmldata[2].tag == 'long_description'
        assert xmldata[2].text == 'This is about how glaives are used in the Yamani Islands'

    def test_dmdsec_from_csv_parsed_metadata_no_data(self):
        data = {}
        # Test
        ret = archivematicaCreateMETS2.createDmdSecsFromCSVParsedMetadata(data)
        # Verify
        assert ret == []

class TestCSVMetadata(TestCase):

    def tearDown(self):
        if os.path.exists('metadata.csv'):
            os.remove('metadata.csv')

    def test_parse_metadata_csv(self):
        # Create metadata.csv
        data = [
            ['Filename', 'dc.title', 'dc.date', 'Other metadata'],
            ['objects/foo.jpg', 'Foo', '2000', 'Taken on a sunny day'],
            ['objects/bar/', 'Bar', '2000', 'All taken on a rainy day'],
        ]
        with open('metadata.csv', 'wb') as f:
            writer = csv.writer(f)
            for row in data:
                writer.writerow(row)

        # Run test
        dc = archivematicaCreateMETSMetadataCSV.parseMetadataCSV('metadata.csv')
        # Verify
        assert dc
        assert 'objects/foo.jpg' in dc
        assert 'dc.title' in dc['objects/foo.jpg']
        assert dc['objects/foo.jpg']['dc.title'] == ['Foo']
        assert 'dc.date' in dc['objects/foo.jpg']
        assert dc['objects/foo.jpg']['dc.date'] == ['2000']
        assert 'Other metadata' in dc['objects/foo.jpg']
        assert dc['objects/foo.jpg']['Other metadata'] == ['Taken on a sunny day']
        assert dc['objects/foo.jpg'].keys() == ['dc.title', 'dc.date', 'Other metadata']

        assert 'objects/bar' in dc
        assert 'dc.title' in dc['objects/bar']
        assert dc['objects/bar']['dc.title'] == ['Bar']
        assert 'dc.date' in dc['objects/bar']
        assert dc['objects/bar']['dc.date'] == ['2000']
        assert 'Other metadata' in dc['objects/bar']
        assert dc['objects/bar']['Other metadata'] == ['All taken on a rainy day']
        assert dc['objects/bar'].keys() == ['dc.title', 'dc.date', 'Other metadata']

    def test_parse_metadata_csv_repeated_columns(self):
        # Create metadata.csv
        data = [
            ['Filename', 'dc.title', 'dc.type', 'dc.type', 'dc.type'],
            ['objects/foo.jpg', 'Foo', 'Photograph', 'Still image', 'Picture'],
        ]
        with open('metadata.csv', 'wb') as f:
            writer = csv.writer(f)
            for row in data:
                writer.writerow(row)

        # Run test
        dc = archivematicaCreateMETSMetadataCSV.parseMetadataCSV('metadata.csv')
        # Verify
        assert dc
        assert 'objects/foo.jpg' in dc
        assert 'dc.title' in dc['objects/foo.jpg']
        assert dc['objects/foo.jpg']['dc.title'] == ['Foo']
        assert 'dc.type' in dc['objects/foo.jpg']
        assert dc['objects/foo.jpg']['dc.type'] == ['Photograph', 'Still image', 'Picture']
        assert dc['objects/foo.jpg'].keys() == ['dc.title', 'dc.type']

    def test_parse_metadata_csv_non_ascii(self):
        # Create metadata.csv
        data = [
            ['Filename', 'dc.title'],
            ['objects/foo.jpg', u'元気です'.encode('utf8')],
        ]
        with open('metadata.csv', 'wb') as f:
            writer = csv.writer(f)
            for row in data:
                writer.writerow(row)

        # Run test
        dc = archivematicaCreateMETSMetadataCSV.parseMetadataCSV('metadata.csv')
        # Verify
        assert dc
        assert 'objects/foo.jpg' in dc
        assert 'dc.title' in dc['objects/foo.jpg']
        assert dc['objects/foo.jpg']['dc.title'] == [u'元気です'.encode('utf8')]
