#!/usr/bin/env python
import os
import shutil
import sys
import tempfile
import uuid

import metsrw
from django.test import TestCase

from main.models import Agent, Event, File, Transfer

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
from create_transfer_mets import write_mets


class TestCreateTransferMETS(TestCase):
    TRANSFER_PATH = r"%transferDirectory%"

    @classmethod
    def setUpTestData(cls):
        cls.root_path = tempfile.mkdtemp(prefix="transfer1-")
        cls.subdir = tempfile.mkdtemp(prefix="subdir1-", dir=cls.root_path)
        cls.empty_subdir = tempfile.mkdtemp(prefix="subdir2-", dir=cls.root_path)
        _, cls.file1 = tempfile.mkstemp(prefix="file1-", dir=cls.subdir)

        file_obj_path = "".join(
            [
                cls.TRANSFER_PATH,
                os.path.join(os.path.basename(cls.subdir), os.path.basename(cls.file1)),
            ]
        )
        cls.transfer = Transfer.objects.create(
            uuid=uuid.uuid4(), currentlocation=cls.TRANSFER_PATH
        )
        cls.file_obj = File.objects.create(
            uuid=uuid.uuid4(),
            transfer=cls.transfer,
            originallocation=file_obj_path,
            currentlocation=file_obj_path,
            removedtime=None,
            size=113318,
            checksum="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
            checksumtype="SHA-256",
        )
        cls.event = Event.objects.create(
            event_id=uuid.uuid4(),
            file_uuid=cls.file_obj,
            event_type="message digest calculation",
            event_detail='program="python"; module="hashlib.sha256()"',
            event_outcome_detail="d10bbb2cddc343cd50a304c21e67cb9d5937a93bcff5e717de2df65e0a6309d6",
        )
        cls.event_agent = Agent.objects.create(
            identifiertype="preservation system", identifiervalue="Archivematica-1.9"
        )
        cls.event.agents.add(cls.event_agent)

    @classmethod
    def tearDownClass(cls):
        super(TestCreateTransferMETS, cls).tearDownClass()

        # cleanup our temp files
        shutil.rmtree(cls.root_path)

    def setUp(self):
        mets_path = os.path.join(self.root_path, "METS.xml")
        write_mets(
            mets_path,
            self.root_path,
            "transferDirectory",
            "transfer_id",
            self.transfer.uuid,
        )
        self.mets_doc = metsrw.METSDocument.fromfile(mets_path)

    def test_transfer_mets_structmap_format(self):
        mets_xml = self.mets_doc.serialize()

        assert len(self.mets_doc.all_files()) == 4

        structmap_types = mets_xml.xpath(
            ".//mets:structMap/@TYPE", namespaces=mets_xml.nsmap
        )
        root_div_labels = mets_xml.xpath(
            ".//mets:structMap/mets:div/@LABEL", namespaces=mets_xml.nsmap
        )
        subdir_div_labels = mets_xml.xpath(
            ".//mets:structMap/mets:div/mets:div/@LABEL", namespaces=mets_xml.nsmap
        )
        file_div_labels = mets_xml.xpath(
            ".//mets:structMap/mets:div/mets:div/mets:div/@LABEL",
            namespaces=mets_xml.nsmap,
        )
        file_ids = mets_xml.xpath(
            ".//mets:structMap/mets:div/mets:div/mets:div/mets:fptr/@FILEID",
            namespaces=mets_xml.nsmap,
        )

        # Test that we have physical and logical structmaps
        assert len(structmap_types) == 2
        assert "physical" in structmap_types
        assert "logical" in structmap_types

        # Test that our physical structmap is labeled properly.
        assert root_div_labels[0] == os.path.basename(self.root_path)
        assert subdir_div_labels[0] == os.path.basename(self.subdir)
        assert file_div_labels[0] == os.path.basename(self.file1)
        assert file_ids[0] == "file-{}".format(self.file_obj.uuid)

        # Test that both (empty and not empty) dirs show up in logical structmap
        assert subdir_div_labels[1] == os.path.basename(self.subdir)
        assert subdir_div_labels[2] == os.path.basename(self.empty_subdir)
