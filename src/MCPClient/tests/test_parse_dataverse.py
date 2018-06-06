# -*- coding: utf8
import os
import sys

from django.test import TestCase
import metsrw

from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))
import parse_dataverse

class TestParseDataverse(TestCase):

    fixture_files = ['dataverse_sip.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    def setUp(self):
        self.mets = metsrw.METSDocument.fromfile(os.path.join(THIS_DIR, 'fixtures', 'dataverse', 'metadata', 'METS.xml'))
        self.uuid = '6741c782-f22b-47b3-8bcf-72fd0c94e195'
        self.unit_path = os.path.join(THIS_DIR, 'fixtures', 'dataverse', '')

        # Clear agents
        models.Agent.objects.all().delete()

    def test_fixture(self):
        assert models.Transfer.objects.count() == 1
        assert models.File.objects.count() == 9

    def test_mapping(self):
        mapping = parse_dataverse.get_db_objects(self.mets, self.uuid)
        assert len(mapping) == 6  # FIXME set to 7 when .RData in METS
        # chelen_052.jpg
        assert self.mets.get_file(file_uuid='2bd13f12-cd98-450d-8c49-416e9f666a9c') in mapping
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/chelan_052.jpg') in mapping.values()
        # Weather_data.sav
        assert self.mets.get_file(file_uuid='fb3b1250-5e45-499f-b0b1-0f6a20d77366') in mapping
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_data.sav') in mapping.values()
        # Weather_data.tab
        assert self.mets.get_file(file_uuid='e5fde5cb-a5d7-4e67-ae66-20b73552eedf') in mapping
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_data.tab') in mapping.values()
        # Weather_data.RData
        # FIXME uncomment when .RData in METS
        # assert self.mets.get_file(file_uuid='a001048d-4c3e-485d-af02-1d19584a93b1') in mapping
        # assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_data.RData') in mapping.values()
        # ris
        assert self.mets.get_file(file_uuid='e9e0d762-feff-4b9c-9f70-b408c47149bc') in mapping
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_datacitation-ris.ris') in mapping.values()
        # ddi
        assert self.mets.get_file(file_uuid='3dfc2e3f-22e2-4d3e-9913-e4bccc5257ff') in mapping
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_data-ddi.xml') in mapping.values()
        # endnote
        assert self.mets.get_file(file_uuid='d9b4e460-f306-43ce-8ee5-7f969595e4ab') in mapping
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_datacitation-endnote.xml') in mapping.values()

    def test_set_filegroups(self):
        """
        It should set the same filegroup for all files in the bundle.
        """
        assert models.File.objects.exclude(filegrpuse='original').count() == 0
        mapping = parse_dataverse.get_db_objects(self.mets, self.uuid)
        parse_dataverse.update_file_use(mapping)
        # Original
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/chelan_052.jpg').filegrpuse == 'original'
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_data.sav').filegrpuse == 'original'
        # Derivative
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_data.tab').filegrpuse == 'derivative'
        # FIXME uncomment when .RData in METS
        # assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_data.RData').filegrpuse == 'derivative'
        # Metadata
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_datacitation-ris.ris').filegrpuse == 'metadata'
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_data-ddi.xml').filegrpuse == 'metadata'
        assert models.File.objects.get(currentlocation='%transferDirectory%objects/Weather_data.zip-2015-11-05T16_06_49.498453/Weather_datacitation-endnote.xml').filegrpuse == 'metadata'

    def test_parse_agent(self):
        """
        It should add a Dataverse agent.
        """
        assert models.Agent.objects.count() == 0
        agent_id = parse_dataverse.add_external_agents(self.unit_path)
        assert models.Agent.objects.count() == 1
        assert agent_id
        agent = models.Agent.objects.all()[0]
        assert agent.identifiertype == 'URI'
        assert agent.identifiervalue == 'http://dataverse.example.com/dvn/'
        assert agent.name == 'Example Dataverse Network'
        assert agent.agenttype == 'organization'

    def test_parse_agent_already_exists(self):
        """
        It should not add a duplicate agent.
        """
        models.Agent.objects.create(
            identifiertype='URI',
            identifiervalue='http://dataverse.example.com/dvn/',
            name='Example Dataverse Network',
            agenttype='organization',
        )
        assert models.Agent.objects.count() == 1
        agent_id = parse_dataverse.add_external_agents(self.unit_path)
        assert models.Agent.objects.count() == 1
        assert agent_id
        agent = models.Agent.objects.all()[0]
        assert agent.identifiertype == 'URI'
        assert agent.identifiervalue == 'http://dataverse.example.com/dvn/'
        assert agent.name == 'Example Dataverse Network'
        assert agent.agenttype == 'organization'

    def test_parse_agent_no_agents(self):
        """
        It should return None
        """
        assert models.Agent.objects.count() == 0
        agent_id = parse_dataverse.add_external_agents(os.path.join(THIS_DIR, 'fixtures', 'emptysip', ''))
        assert models.Agent.objects.count() == 0
        assert agent_id is None

    def test_parse_derivative(self):
        """
        It should create a Derivation for the tabfile and related.
        """
        assert models.Derivation.objects.count() == 0
        mapping = parse_dataverse.get_db_objects(self.mets, self.uuid)
        agent = parse_dataverse.add_external_agents(self.unit_path)
        parse_dataverse.create_derivatives(mapping, agent)
        assert models.Event.objects.count() == 1  # FIXME set to 2 when .RData in METS
        assert models.Derivation.objects.count() == 1  # FIXME set to 2 when .RData in METS
        # FIXME Uncomment when .RData in METS
        # assert models.Derivation.objects.get(source_file_id='e2834eed-4178-469a-9a4e-c8f1490bb804', derived_file_id='071e6af9-f676-40fa-a5ab-754ca6b653e0', event__isnull=False)
        assert models.Derivation.objects.get(source_file_id='e2834eed-4178-469a-9a4e-c8f1490bb804', derived_file_id='5518a927-bae9-497c-8a16-caa072e6ef7e', event__isnull=False)

    def test_validate_checksums(self):
        """
        It should do something with checksums to validate them??
        """
        assert models.Event.objects.count() == 0
        mapping = parse_dataverse.get_db_objects(self.mets, self.uuid)
        parse_dataverse.validate_checksums(mapping, self.unit_path)
        # assert models.Event.objects.count() == 2
        e = models.Event.objects.get(file_uuid_id='22fade0b-d2fc-4835-b669-970c8fdd9b76')
        assert e.event_type == 'fixity check'
        assert e.event_detail == 'program="python"; module="hashlib.md5()"'
        assert e.event_outcome == 'Pass'
        assert e.event_outcome_detail == 'Dataverse checksum 7ede51390fe3f01fb13632c001d2499d verified'
        e = models.Event.objects.get(file_uuid_id='e2834eed-4178-469a-9a4e-c8f1490bb804')
        assert e.event_type == 'fixity check'
        assert e.event_detail == 'program="python"; module="hashlib.md5()"'
        assert e.event_outcome == 'Pass'
        assert e.event_outcome_detail == 'Dataverse checksum 4ca2a78963445bce067e027e10394b61 verified'
