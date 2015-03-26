# -*- coding: utf8
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

    def test_get_dublincore(self):
        sipuuid = '8b891d7c-5bd2-4249-84a1-2f00f725b981'
        siptypeuuid = '3e48343d-e2d2-4956-aaa3-b54d26eb9761'

        # Generate DC element from DB
        dc_elem = archivematicaCreateMETS2.getDublinCore(siptypeuuid, sipuuid)

        # Verify created correctly
        assert dc_elem
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
        siptypeuuid = '3e48343d-e2d2-4956-aaa3-b54d26eb9761'

        dc_elem = archivematicaCreateMETS2.getDublinCore(siptypeuuid, sipuuid)
        assert dc_elem is None

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
