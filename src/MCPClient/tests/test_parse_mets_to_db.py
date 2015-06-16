# -*- coding: utf8
from lxml import etree
import os
import sys

from django.test import TestCase

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))
import parse_mets_to_db

import fpr
from main import models

class TestParseFiles(TestCase):
    """ Test parsing file information from a METS file to the DB. """

    fixture_files = ['formats.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    def setUp(self):
        self.ORIG_INFO = {
            'uuid': 'ae8d4290-fe52-4954-b72a-0f591bee2e2f',
            'original_path': "%SIPDirectory%objects/evelyn's photo.jpg",
            'current_path': '%SIPDirectory%objects/evelyn_s_photo.jpg',
            'use': 'original',
            'checksum': 'd2bed92b73c7090bb30a0b30016882e7069c437488e1513e9deaacbe29d38d92',
            'size': '158131',
            'format_version': fpr.models.FormatVersion.objects.get(uuid='01fac958-274d-41ef-978f-d9cf711b3c4a'),
            'derivation': '8140ebe5-295c-490b-a34a-83955b7c844e',
            'derivation_event': '0ce13092-911f-4a89-b9e1-0e61921a03d4',
        }
        self.PRES_INFO = {
            'uuid': '8140ebe5-295c-490b-a34a-83955b7c844e',
            'original_path': "%SIPDirectory%objects/evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif",
            'current_path': '%SIPDirectory%objects/evelyn_s_photo-6383b731-99e0-432d-a911-a0d2dfd1ce76.tif',
            'use': 'preservation',
            'checksum': 'd82448f154b9185bc777ecb0a3602760eb76ba85dd3098f073b2c91a03f571e9',
            'size': '1446772',
            'format_version': fpr.models.FormatVersion.objects.get(uuid='2ebdfa17-2257-49f8-8035-5f304bb46918'),
            'derivation': None,
            'derivation_event': None,
        }
        self.METS_INFO = {
            'uuid': '590bd882-7521-498c-8f89-0958218f779d',
            'original_path': "%SIPDirectory%objects/submissionDocumentation/transfer-no-metadata-46260807-ece1-4a0e-b70a-9814c701146b/METS.xml",
            'current_path': '%SIPDirectory%objects/submissionDocumentation/transfer-no-metadata-46260807-ece1-4a0e-b70a-9814c701146b/METS.xml',
            'use': 'submissionDocumentation',
            'checksum': '51132e5ce1b5d2c2c363f05495f447ea924ab29c2cda2c11037b5fca2119e45a',
            'size': '12222',
            'format_version': fpr.models.FormatVersion.objects.get(uuid='d60e5243-692e-4af7-90cd-40c53cb8dc7d'),
            'derivation': None,
            'derivation_event': None,
        }
        self.SIP_UUID = '8a0cac37-e446-4fa7-9e96-062bf07ccd04'
        models.SIP.objects.create(uuid=self.SIP_UUID, sip_type='AIP-REIN')

    def test_parse_file_info(self):
        """
        It should parse file info into a dict.
        It should attach derivation information to the original file.
        """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'))
        files = parse_mets_to_db.parse_files(root)
        assert len(files) == 3
        orig = files[0]
        assert orig['uuid'] == self.ORIG_INFO['uuid']
        assert orig['original_path'] == self.ORIG_INFO['original_path']
        assert orig['current_path'] == self.ORIG_INFO['current_path']
        assert orig['use'] == self.ORIG_INFO['use']
        assert orig['checksum'] == self.ORIG_INFO['checksum']
        assert orig['size'] == self.ORIG_INFO['size']
        assert orig['format_version'] == self.ORIG_INFO['format_version']
        assert orig['derivation'] == self.ORIG_INFO['derivation']
        assert orig['derivation_event'] == self.ORIG_INFO['derivation_event']
        mets = files[1]
        assert mets['uuid'] == self.METS_INFO['uuid']
        assert mets['original_path'] == self.METS_INFO['original_path']
        assert mets['current_path'] == self.METS_INFO['current_path']
        assert mets['use'] == self.METS_INFO['use']
        assert mets['checksum'] == self.METS_INFO['checksum']
        assert mets['size'] == self.METS_INFO['size']
        assert mets['format_version'] == self.METS_INFO['format_version']
        assert mets['derivation'] == self.METS_INFO['derivation']
        assert mets['derivation_event'] == self.METS_INFO['derivation_event']
        pres = files[2]
        assert pres['uuid'] == self.PRES_INFO['uuid']
        assert pres['original_path'] == self.PRES_INFO['original_path']
        assert pres['current_path'] == self.PRES_INFO['current_path']
        assert pres['use'] == self.PRES_INFO['use']
        assert pres['checksum'] == self.PRES_INFO['checksum']
        assert pres['size'] == self.PRES_INFO['size']
        assert pres['format_version'] == self.PRES_INFO['format_version']
        assert pres['derivation'] == self.PRES_INFO['derivation']
        assert pres['derivation_event'] == self.PRES_INFO['derivation_event']

    def test_insert_file_info(self):
        """ It should insert file info into the DB. """
        files = [self.METS_INFO, self.PRES_INFO, self.ORIG_INFO]
        parse_mets_to_db.update_files(self.SIP_UUID, files)
        # Verify original file
        orig = models.File.objects.get(uuid=self.ORIG_INFO['uuid'])
        assert orig.sip_id == self.SIP_UUID
        assert orig.transfer is None
        assert orig.originallocation == self.ORIG_INFO['original_path']
        assert orig.currentlocation == self.ORIG_INFO['current_path']
        assert orig.filegrpuse == self.ORIG_INFO['use']
        assert orig.filegrpuuid == ''
        assert orig.checksum == self.ORIG_INFO['checksum']
        assert orig.size == int(self.ORIG_INFO['size'])
        assert models.Event.objects.get(file_uuid_id=self.ORIG_INFO['uuid'], event_type='reingestion')
        assert models.FileFormatVersion.objects.get(file_uuid_id=self.ORIG_INFO['uuid'], format_version=self.ORIG_INFO['format_version'])
        assert models.Derivation.objects.get(source_file_id=self.ORIG_INFO['uuid'], derived_file=self.PRES_INFO['uuid'])
        # Verify preservation file
        pres = models.File.objects.get(uuid=self.PRES_INFO['uuid'])
        assert pres.sip_id == self.SIP_UUID
        assert pres.transfer is None
        assert pres.originallocation == self.PRES_INFO['original_path']
        assert pres.currentlocation == self.PRES_INFO['current_path']
        assert pres.filegrpuse == self.PRES_INFO['use']
        assert pres.filegrpuuid == ''
        assert pres.checksum == self.PRES_INFO['checksum']
        assert pres.size == int(self.PRES_INFO['size'])
        assert models.Event.objects.get(file_uuid_id=self.PRES_INFO['uuid'], event_type='reingestion')
        assert models.FileFormatVersion.objects.get(file_uuid_id=self.PRES_INFO['uuid'], format_version=self.PRES_INFO['format_version'])
        # Verify original file
        mets = models.File.objects.get(uuid=self.METS_INFO['uuid'])
        assert mets.sip_id == self.SIP_UUID
        assert mets.transfer is None
        assert mets.originallocation == self.METS_INFO['original_path']
        assert mets.currentlocation == self.METS_INFO['current_path']
        assert mets.filegrpuse == self.METS_INFO['use']
        assert mets.filegrpuuid == ''
        assert mets.checksum == self.METS_INFO['checksum']
        assert mets.size == int(self.METS_INFO['size'])
        assert models.Event.objects.get(file_uuid_id=self.METS_INFO['uuid'], event_type='reingestion')
        assert models.FileFormatVersion.objects.get(file_uuid_id=self.METS_INFO['uuid'], format_version=self.METS_INFO['format_version'])
        assert models.Derivation.objects.filter(source_file_id=self.METS_INFO['uuid']).exists() is False
        assert models.Derivation.objects.filter(derived_file=self.METS_INFO['uuid']).exists() is False
