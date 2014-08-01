# -*- coding: utf8
import datetime
from lxml import etree
import os
import sys

from django.test import TestCase

from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))
import archivematicaCreateMETSReingest

NSMAP = {
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'mets': 'http://www.loc.gov/METS/',
    'premis': 'info:lc/xmlns/premis-v2',
}
REMOVE_BLANK_PARSER = etree.XMLParser(remove_blank_text=True)


class TestUpdateDublinCore(TestCase):
    """ Test updating SIP-level DublinCore. (update_dublincore) """

    fixture_files = ['dublincore.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat('T')

    sip_uuid_none = 'dnedne7c-5bd2-4249-84a1-2f00f725b981'
    sip_uuid_original = '8b891d7c-5bd2-4249-84a1-2f00f725b981'
    sip_uuid_reingest = '87d30df4-63f5-434b-9da6-25aa995de6fe'
    sip_uuid_updated = '5d78a2a5-57a6-430f-87b2-b89fb3ccb050'

    def test_no_dc(self):
        """ It should do nothing if there is no DC entry. """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'))
        assert root.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP) is None
        root = archivematicaCreateMETSReingest.update_dublincore(root, self.sip_uuid_none, self.now)
        assert root.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP) is None

    def test_dc_not_updated(self):
        """ It should do nothing if the DC has not been modified. """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'))
        assert root.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP) is None
        root = archivematicaCreateMETSReingest.update_dublincore(root, self.sip_uuid_reingest, self.now)
        assert root.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP) is None

    def test_new_dc(self):
        """
        It should add a new DC if there was none before.
        It should add after the metsHdr if no dmdSecs exist.
        """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'))
        assert root.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP) is None
        root = archivematicaCreateMETSReingest.update_dublincore(root, self.sip_uuid_original, self.now)
        assert root.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP) is not None
        dmdsec = root.find('mets:dmdSec', namespaces=NSMAP)
        assert dmdsec.attrib['CREATED'] == self.now
        # Verify fileSec div updated
        assert root.find('mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]', namespaces=NSMAP).attrib['DMDID'] == dmdsec.attrib['ID']
        # Verify DC correct
        dc_elem = root.find('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]/mets:xmlData/dcterms:dublincore', namespaces=NSMAP)
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

    def test_update_existing_dc(self):
        """
        It should add a new updated DC and mark the old one as original.
        It should ignore file-level DC.
        It should add after the last dmdSec.
        """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_sip_and_file_dc.xml'), parser=REMOVE_BLANK_PARSER)
        assert len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)) == 4
        root = archivematicaCreateMETSReingest.update_dublincore(root, self.sip_uuid_updated, self.now)
        assert len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)) == 5
        # Verify file-level DC not updated
        assert root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP).get('STATUS') is None
        assert root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP).get('STATUS') is None
        assert root.find('mets:dmdSec[@ID="dmdSec_3"]', namespaces=NSMAP).get('STATUS') is None
        # Verify original SIP-level marked as original
        assert root.find('mets:dmdSec[@ID="dmdSec_4"]', namespaces=NSMAP).attrib['STATUS'] == 'original'
        # Verify dmdSec created
        dmdsec = root.xpath('mets:dmdSec[not(@ID="dmdSec_1" or @ID="dmdSec_2" or @ID="dmdSec_3" or @ID="dmdSec_4")]', namespaces=NSMAP)[0]
        assert dmdsec.attrib['STATUS'] == 'updated'
        assert dmdsec.attrib['CREATED'] == self.now
        # Verify fileSec div updated
        assert dmdsec.attrib['ID'] in root.find('mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]', namespaces=NSMAP).attrib['DMDID']
        assert 'dmdSec_4' in root.find('mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]', namespaces=NSMAP).attrib['DMDID']
        # Verify new DC
        dc_elem = dmdsec.find('.//dcterms:dublincore', namespaces=NSMAP)
        assert len(dc_elem) == 12
        assert dc_elem[0].tag == '{http://purl.org/dc/elements/1.1/}title'
        assert dc_elem[0].text == 'Yamani Weapons'
        assert dc_elem[1].tag == '{http://purl.org/dc/elements/1.1/}creator'
        assert dc_elem[1].text == 'Keladry of Mindelan'
        assert dc_elem[2].tag == '{http://purl.org/dc/elements/1.1/}subject'
        assert dc_elem[2].text == 'Glaives'
        assert dc_elem[3].tag == '{http://purl.org/dc/elements/1.1/}description'
        assert dc_elem[3].text == 'Glaives are awesome'
        assert dc_elem[4].tag == '{http://purl.org/dc/elements/1.1/}publisher'
        assert dc_elem[4].text == 'Tortall Press'
        assert dc_elem[5].tag == '{http://purl.org/dc/elements/1.1/}contributor'
        assert dc_elem[5].text == 'Yuki, Neal'
        assert dc_elem[6].tag == '{http://purl.org/dc/elements/1.1/}type'
        assert dc_elem[6].text == 'Archival Information Package'
        assert dc_elem[7].tag == '{http://purl.org/dc/elements/1.1/}format'
        assert dc_elem[7].text == 'palimpsest'
        assert dc_elem[8].tag == '{http://purl.org/dc/elements/1.1/}identifier'
        assert dc_elem[8].text == '42/1'
        assert dc_elem[9].tag == '{http://purl.org/dc/elements/1.1/}language'
        assert dc_elem[9].text == 'en'
        assert dc_elem[10].tag == '{http://purl.org/dc/elements/1.1/}coverage'
        assert dc_elem[10].text == 'Partial'
        assert dc_elem[11].tag == '{http://purl.org/dc/elements/1.1/}rights'
        assert dc_elem[11].text == 'Public Domain'

    def test_update_reingested_dc(self):
        """
        It should add a new DC if old ones exist.
        It should not mark other reingested DC as original.
        """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_multiple_sip_dc.xml'), parser=REMOVE_BLANK_PARSER)
        assert len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)) == 2
        root = archivematicaCreateMETSReingest.update_dublincore(root, self.sip_uuid_updated, self.now)
        assert len(root.findall('mets:dmdSec/mets:mdWrap[@MDTYPE="DC"]', namespaces=NSMAP)) == 3
        # Verify existing DC marked as original
        assert root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP).get('STATUS') == 'original'
        assert root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP).get('STATUS') == 'updated'
        # Verify dmdSec created
        dmdsec = root.xpath('mets:dmdSec[not(@ID="dmdSec_1" or @ID="dmdSec_2")]', namespaces=NSMAP)[0]
        assert dmdsec.attrib['STATUS'] == 'updated'
        assert dmdsec.attrib['CREATED'] == self.now
        # Verify fileSec div updated
        assert dmdsec.attrib['ID'] in root.find('mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]', namespaces=NSMAP).attrib['DMDID']
        assert 'dmdSec_1' in root.find('mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]', namespaces=NSMAP).attrib['DMDID']
        assert 'dmdSec_2' in root.find('mets:structMap/mets:div[@TYPE="Directory"]/mets:div[@TYPE="Directory"][@LABEL="objects"]', namespaces=NSMAP).attrib['DMDID']
        # Verify new DC
        dc_elem = dmdsec.find('.//dcterms:dublincore', namespaces=NSMAP)
        assert len(dc_elem) == 12
        assert dc_elem[0].tag == '{http://purl.org/dc/elements/1.1/}title'
        assert dc_elem[0].text == 'Yamani Weapons'
        assert dc_elem[1].tag == '{http://purl.org/dc/elements/1.1/}creator'
        assert dc_elem[1].text == 'Keladry of Mindelan'
        assert dc_elem[2].tag == '{http://purl.org/dc/elements/1.1/}subject'
        assert dc_elem[2].text == 'Glaives'
        assert dc_elem[3].tag == '{http://purl.org/dc/elements/1.1/}description'
        assert dc_elem[3].text == 'Glaives are awesome'
        assert dc_elem[4].tag == '{http://purl.org/dc/elements/1.1/}publisher'
        assert dc_elem[4].text == 'Tortall Press'
        assert dc_elem[5].tag == '{http://purl.org/dc/elements/1.1/}contributor'
        assert dc_elem[5].text == 'Yuki, Neal'
        assert dc_elem[6].tag == '{http://purl.org/dc/elements/1.1/}type'
        assert dc_elem[6].text == 'Archival Information Package'
        assert dc_elem[7].tag == '{http://purl.org/dc/elements/1.1/}format'
        assert dc_elem[7].text == 'palimpsest'
        assert dc_elem[8].tag == '{http://purl.org/dc/elements/1.1/}identifier'
        assert dc_elem[8].text == '42/1'
        assert dc_elem[9].tag == '{http://purl.org/dc/elements/1.1/}language'
        assert dc_elem[9].text == 'en'
        assert dc_elem[10].tag == '{http://purl.org/dc/elements/1.1/}coverage'
        assert dc_elem[10].text == 'Partial'
        assert dc_elem[11].tag == '{http://purl.org/dc/elements/1.1/}rights'
        assert dc_elem[11].text == 'Public Domain'


class TestUpdateRights(TestCase):
    """ Test updating PREMIS:RIGHTS. (update_rights and add_rights_elements) """

    fixture_files = ['rights.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat('T')

    sip_uuid_none = 'dnedne7c-5bd2-4249-84a1-2f00f725b981'
    sip_uuid_original = 'a4a5480c-9f51-4119-8dcb-d3f12e647c14'
    sip_uuid_reingest = '10d57d98-29e5-4b2c-9f9f-d163e632eb31'
    sip_uuid_updated = '2941f14c-bd57-4f4a-a514-a3bf6ac5adf0'

    def test_no_rights(self):
        """ It should do nothing if there are no rights entries. """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'), parser=REMOVE_BLANK_PARSER)
        assert root.find('mets:amdSec/mets:rightsMD', namespaces=NSMAP) is None
        root = archivematicaCreateMETSReingest.update_rights(root, self.sip_uuid_none, self.now)
        assert root.find('mets:amdSec/mets:rightsMD', namespaces=NSMAP) is None

    def test_rights_not_updated(self):
        """ It should do nothing if the rights have not been modified. """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'), parser=REMOVE_BLANK_PARSER)
        assert root.find('mets:amdSec/mets:rightsMD', namespaces=NSMAP) is None
        root = archivematicaCreateMETSReingest.update_rights(root, self.sip_uuid_reingest, self.now)
        assert root.find('mets:amdSec/mets:rightsMD', namespaces=NSMAP) is None

    def test_new_rights(self):
        """
        It should add a new rights if there were none before.
        It should add after the last techMD.
        It should add rights to all original files.
        It should not add rights to the METS file amdSec.
        """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'), parser=REMOVE_BLANK_PARSER)
        assert root.find('mets:amdSec/mets:rightsMD', namespaces=NSMAP) is None
        root = archivematicaCreateMETSReingest.update_rights(root, self.sip_uuid_original, self.now)

        # Verify new rightsMD for all rightsstatements
        assert len(root.findall('mets:amdSec/mets:rightsMD', namespaces=NSMAP)) == 4
        # Verify all associated with the original file
        assert len(root.findall('mets:amdSec[@ID="amdSec_2"]/mets:rightsMD', namespaces=NSMAP)) == 4
        # Verify rightsMDs exist with correct basis
        assert root.xpath('.//premis:rightsBasis[text()="Copyright"]', namespaces=NSMAP)[0] is not None
        assert root.xpath('.//premis:rightsBasis[text()="Statute"]', namespaces=NSMAP)[0] is not None
        assert root.xpath('.//premis:rightsBasis[text()="License"]', namespaces=NSMAP)[0] is not None
        assert root.xpath('.//premis:rightsBasis[text()="Other"]', namespaces=NSMAP)[0] is not None

    def test_update_existing_rights(self):
        """
        It should add new updated rights and mark the old ones as superseded.
        It should add after the last rightsMD.
        It should add rights to all files.
        It should not add rights to the METS file.
        """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_all_rights.xml'), parser=REMOVE_BLANK_PARSER)
        assert len(root.findall('mets:amdSec/mets:rightsMD', namespaces=NSMAP)) == 5
        root = archivematicaCreateMETSReingest.update_rights(root, self.sip_uuid_updated, self.now)

        # Verify new rightsMD for all rightsstatements
        assert len(root.findall('mets:amdSec/mets:rightsMD', namespaces=NSMAP)) == 6
        # Verify all associated with the original file
        assert len(root.findall('mets:amdSec[@ID="amdSec_1"]/mets:rightsMD', namespaces=NSMAP)) == 6
        assert root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_1"]', namespaces=NSMAP).get('STATUS') is None
        assert root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_2"]', namespaces=NSMAP).attrib['STATUS'] == 'superseded'
        assert root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_3"]', namespaces=NSMAP).get('STATUS') is None
        assert root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_4"]', namespaces=NSMAP).get('STATUS') is None
        assert root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_5"]', namespaces=NSMAP).get('STATUS') is None
        new_rights = root.find('mets:amdSec[@ID="amdSec_1"]', namespaces=NSMAP)[6]
        assert new_rights is not None
        assert new_rights.attrib['STATUS'] == 'current'
        assert new_rights.attrib['CREATED'] == self.now
        assert new_rights.find('.//premis:statuteApplicableDates/premis:endDate', namespaces=NSMAP).text == '2054'
        assert new_rights.find('.//premis:termOfRestriction/premis:endDate', namespaces=NSMAP).text == '2054'
        assert new_rights.find('.//premis:statuteNote', namespaces=NSMAP).text == 'SIN'

    def test_update_reingested_rights(self):
        """
        It should add new updated rights and mark all the old ones as superseded.
        It should add after the last rightsMD.
        It should add rights to all files.
        It should not add rights to the METS file.
        """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_updated_rights.xml'), parser=REMOVE_BLANK_PARSER)
        assert len(root.findall('mets:amdSec/mets:rightsMD', namespaces=NSMAP)) == 2
        root = archivematicaCreateMETSReingest.update_rights(root, self.sip_uuid_updated, self.now)

        # Verify new rightsMD for all rightsstatements
        assert len(root.findall('mets:amdSec/mets:rightsMD', namespaces=NSMAP)) == 3
        # Verify all associated with the original file
        assert len(root.findall('mets:amdSec[@ID="amdSec_1"]/mets:rightsMD', namespaces=NSMAP)) == 3
        assert root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_1"]', namespaces=NSMAP).attrib['STATUS'] == 'superseded'
        assert root.find('mets:amdSec/mets:rightsMD[@ID="rightsMD_2"]', namespaces=NSMAP).attrib['STATUS'] == 'superseded'
        new_rights = root.find('mets:amdSec[@ID="amdSec_1"]', namespaces=NSMAP)[3]
        assert new_rights is not None
        assert new_rights.attrib['STATUS'] == 'current'
        assert new_rights.attrib['CREATED'] == self.now
        assert new_rights.find('.//premis:statuteApplicableDates/premis:endDate', namespaces=NSMAP).text == '2054'
        assert new_rights.find('.//premis:termOfRestriction/premis:endDate', namespaces=NSMAP).text == '2054'
        assert new_rights.find('.//premis:statuteNote', namespaces=NSMAP).text == 'SIN'


class TestAddEvents(TestCase):
    """ Test adding reingest events to all existing files. (add_events) """

    fixture_files = ['sip.json', 'files.json', 'agents.json', 'reingest_events.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    sip_uuid = '4060ee97-9c3f-4822-afaf-ebdf838284c3'

    def test_all_files_get_events(self):
        """
        It should add reingestion events to all files.
        It should not change Agent information.
        """
        models.Agent.objects.all().delete()
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'))
        assert len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP)) == 16
        assert len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP)) == 9
        root = archivematicaCreateMETSReingest.add_events(root, self.sip_uuid)
        assert len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP)) == 19
        assert root.xpath('mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="reingestion"]', namespaces=NSMAP) != []
        assert root.xpath('mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="reingestion"]', namespaces=NSMAP) != []
        assert root.xpath('mets:amdSec[@ID="amdSec_3"]//premis:eventType[text()="reingestion"]', namespaces=NSMAP) != []
        assert len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP)) == 9

    def test_agent_not_in_mets(self):
        """ It should add a new Agent if it doesn't already exist. """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'))
        assert len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP)) == 16
        assert len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP)) == 9
        root = archivematicaCreateMETSReingest.add_events(root, self.sip_uuid)
        assert len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:EVENT"]', namespaces=NSMAP)) == 19
        assert len(root.findall('.//mets:mdWrap[@MDTYPE="PREMIS:AGENT"]', namespaces=NSMAP)) == 12
        assert root.xpath('mets:amdSec[@ID="amdSec_1"]//premis:eventType[text()="reingestion"]', namespaces=NSMAP) != []
        assert root.xpath('mets:amdSec[@ID="amdSec_1"]//premis:agentIdentifierValue[text()="Archivematica-1.4.0"]', namespaces=NSMAP) != []
        assert root.xpath('mets:amdSec[@ID="amdSec_2"]//premis:eventType[text()="reingestion"]', namespaces=NSMAP) != []
        assert root.xpath('mets:amdSec[@ID="amdSec_2"]//premis:agentIdentifierValue[text()="Archivematica-1.4.0"]', namespaces=NSMAP) != []
        assert root.xpath('mets:amdSec[@ID="amdSec_3"]//premis:eventType[text()="reingestion"]', namespaces=NSMAP) != []
        assert root.xpath('mets:amdSec[@ID="amdSec_3"]//premis:agentIdentifierValue[text()="Archivematica-1.4.0"]', namespaces=NSMAP) != []


class TestAddingNewFiles(TestCase):
    """ Test adding new metadata files to the structMap & fileSec. (add_new_files) """

    fixture_files = ['sip.json', 'files.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    sip_uuid = '4060ee97-9c3f-4822-afaf-ebdf838284c3'
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat('T')

    def test_no_new_files(self):
        """ It should not modify the fileSec or structMap if there are no new files. """
        # Make sure directory is empty
        sip_dir = os.path.join(THIS_DIR, 'fixtures', 'emptysip', '')
        try:
            os.remove(os.path.join(sip_dir, 'objects', 'metadata', 'transfers', '.gitignore'))
        except OSError:
            pass
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'))
        assert len(root.findall('mets:amdSec', namespaces=NSMAP)) == 3
        assert len(root.findall('mets:fileSec//mets:file', namespaces=NSMAP)) == 3
        assert root.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP) is None
        assert len(root.findall('mets:structMap//mets:div', namespaces=NSMAP)) == 10

        root = archivematicaCreateMETSReingest.add_new_files(root, self.sip_uuid, sip_dir, self.now)
        assert len(root.findall('mets:amdSec', namespaces=NSMAP)) == 3
        assert len(root.findall('mets:fileSec//mets:file', namespaces=NSMAP)) == 3
        assert root.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP) is None
        assert len(root.findall('mets:structMap//mets:div', namespaces=NSMAP)) == 10

        # Reverse deletion
        with open(os.path.join(sip_dir, 'objects', 'metadata', 'transfers', '.gitignore'), 'w'):
            pass

    def test_add_metadata_csv(self):
        """
        It should add a metadata file to the fileSec, structMap & amdSec.
        It should add a dmdSec.  (Other testing for TestUpdateMetadataCSV)
        """
        sip_dir = os.path.join(THIS_DIR, 'fixtures', 'metadata_csv_sip', '')
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'))
        assert len(root.findall('mets:amdSec', namespaces=NSMAP)) == 3
        assert len(root.findall('mets:fileSec//mets:file', namespaces=NSMAP)) == 3
        assert root.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP) is None
        assert len(root.findall('mets:structMap//mets:div', namespaces=NSMAP)) == 10

        root = archivematicaCreateMETSReingest.add_new_files(root, self.sip_uuid, sip_dir, self.now)

        file_uuid = '66370f14-2f64-4750-9d50-547614be40e8'
        # Check structMap
        div = root.find('mets:structMap/mets:div/mets:div[@LABEL="objects"]/mets:div[@LABEL="metadata"]/mets:div[@TYPE="Item"]', namespaces=NSMAP)
        assert div is not None
        assert div.attrib['LABEL'] == 'metadata.csv'
        assert len(div) == 1
        assert div[0].tag == '{http://www.loc.gov/METS/}fptr'
        assert div[0].attrib['FILEID'] == 'file-' + file_uuid
        # Check fileSec
        mets_grp = root.find('mets:fileSec/mets:fileGrp[@USE="metadata"]', namespaces=NSMAP)
        assert mets_grp is not None
        assert len(mets_grp) == 1
        assert mets_grp[0].tag == '{http://www.loc.gov/METS/}file'
        assert mets_grp[0].attrib['ID'] == 'file-' + file_uuid
        assert mets_grp[0].attrib['GROUPID'] == 'Group-' + file_uuid
        adm_id = mets_grp[0].attrib['ADMID']
        assert adm_id
        assert len(mets_grp[0]) == 1
        assert mets_grp[0][0].tag == '{http://www.loc.gov/METS/}FLocat'
        assert mets_grp[0][0].attrib['LOCTYPE'] == 'OTHER'
        assert mets_grp[0][0].attrib['OTHERLOCTYPE'] == 'SYSTEM'
        assert mets_grp[0][0].attrib['{http://www.w3.org/1999/xlink}href'] == 'objects/metadata/metadata.csv'
        # Check amdSec
        amdsec = root.find('mets:amdSec[@ID="' + adm_id + '"]', namespaces=NSMAP)
        assert amdsec is not None
        assert amdsec.findtext('.//premis:objectIdentifierValue', namespaces=NSMAP) == file_uuid
        assert amdsec.findtext('.//premis:messageDigest', namespaces=NSMAP) == 'e8121d8a660e2992872f0b67923d2d08dde9a1ba72dfd58e5a31e68fbac3633c'
        assert amdsec.findtext('.//premis:size', namespaces=NSMAP) == '154'
        assert amdsec.findtext('.//premis:originalName', namespaces=NSMAP) == '%SIPDirectory%metadata/metadata.csv'


class TestUpdateMetadataCSV(TestCase):
    """ Test adding metadata.csv-based DC metadata. (update_metadata_csv) """

    fixture_files = ['sip.json', 'files.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    sip_uuid = '4060ee97-9c3f-4822-afaf-ebdf838284c3'
    sip_dir = os.path.join(THIS_DIR, 'fixtures', 'metadata_csv_sip', '')
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat('T')

    def setUp(self):
        self.csv_file = models.File.objects.get(uuid='66370f14-2f64-4750-9d50-547614be40e8')

    def test_new_dmdsecs(self):
        """ It should add file-level dmdSecs. """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_no_metadata.xml'))
        assert len(root.findall('mets:dmdSec', namespaces=NSMAP)) == 0
        root = archivematicaCreateMETSReingest.update_metadata_csv(root, self.csv_file, self.sip_uuid, self.sip_dir, self.now)
        assert len(root.findall('mets:dmdSec', namespaces=NSMAP)) == 1
        dmdsec = root.find('mets:dmdSec', namespaces=NSMAP)
        assert dmdsec.attrib['ID']
        assert dmdsec.attrib['CREATED'] == self.now
        assert dmdsec.attrib['STATUS'] == 'original'
        assert dmdsec.findtext('.//dc:title', namespaces=NSMAP) == 'Mountain Tents'
        assert dmdsec.findtext('.//dc:description', namespaces=NSMAP) == 'Tents on a mountain'

    def test_update_existing(self):
        """
        It should add new dmdSecs.
        It should updated the existing dmdSec as original.
        """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_file_dc.xml'))
        assert len(root.findall('mets:dmdSec', namespaces=NSMAP)) == 1
        root = archivematicaCreateMETSReingest.update_metadata_csv(root, self.csv_file, self.sip_uuid, self.sip_dir, self.now)
        assert len(root.findall('mets:dmdSec', namespaces=NSMAP)) == 2
        orig = root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP)
        assert orig.attrib['STATUS'] == 'original'
        div = root.xpath('.//mets:div[contains(@DMDID,"dmdSec_1")]', namespaces=NSMAP)[0]
        assert div.attrib['DMDID']
        dmdid = div.attrib['DMDID'].split()[1]
        new = root.find('mets:dmdSec[@ID="' + dmdid + '"]', namespaces=NSMAP)
        assert new.attrib['CREATED'] == self.now
        assert new.attrib['STATUS'] == 'updated'
        assert new.findtext('.//dc:title', namespaces=NSMAP) == 'Mountain Tents'
        assert new.findtext('.//dc:description', namespaces=NSMAP) == 'Tents on a mountain'

    def test_update_reingest(self):
        """
        It should add new dmdSecs.
        It should not updated the already updated dmdSecs.
        """
        root = etree.parse(os.path.join(THIS_DIR, 'fixtures', 'mets_file_dc_updated.xml'))
        assert len(root.findall('mets:dmdSec', namespaces=NSMAP)) == 2
        root = archivematicaCreateMETSReingest.update_metadata_csv(root, self.csv_file, self.sip_uuid, self.sip_dir, self.now)
        assert len(root.findall('mets:dmdSec', namespaces=NSMAP)) == 3
        orig = root.find('mets:dmdSec[@ID="dmdSec_1"]', namespaces=NSMAP)
        assert orig.attrib['STATUS'] == 'original'
        updated = root.find('mets:dmdSec[@ID="dmdSec_2"]', namespaces=NSMAP)
        assert updated.attrib['STATUS'] == 'updated'
        div = root.xpath('.//mets:div[contains(@DMDID,"dmdSec_1")]', namespaces=NSMAP)[0]
        assert div.attrib['DMDID']
        dmdid = div.attrib['DMDID'].split()[2]
        new = root.find('mets:dmdSec[@ID="' + dmdid + '"]', namespaces=NSMAP)
        assert new.attrib['CREATED'] == self.now
        assert new.attrib['STATUS'] == 'updated'
        assert new.findtext('.//dc:title', namespaces=NSMAP) == 'Mountain Tents'
        assert new.findtext('.//dc:description', namespaces=NSMAP) == 'Tents on a mountain'
