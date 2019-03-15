#!/usr/bin/env python
from __future__ import unicode_literals

import os
import shutil
import sys
import tempfile
import uuid

import metsrw
import pytest
from django.test import TestCase

from main.models import Agent, Event, File, Transfer

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
from create_transfer_mets import write_mets


@pytest.fixture()
def subdir_path(tmp_path):
    subdir = tmp_path / "subdir1"
    subdir.mkdir()

    return subdir


@pytest.fixture()
def empty_subdir_path(tmp_path):
    empty_subdir = tmp_path / "subdir2-empty"
    empty_subdir.mkdir()

    return empty_subdir


@pytest.fixture()
def file_path(subdir_path):
    file_path = subdir_path / "file1"
    file_path.write_text("Hello world")

    return file_path


@pytest.fixture()
def transfer(db):
    return Transfer.objects.create(
        uuid=uuid.uuid4(), currentlocation=r"%transferDirectory%"
    )


@pytest.fixture()
def file_obj(db, transfer, tmp_path, file_path):
    file_obj_path = "".join(
        [transfer.currentlocation, str(file_path.relative_to(tmp_path))]
    )
    return File.objects.create(
        uuid=uuid.uuid4(),
        transfer=transfer,
        originallocation=file_obj_path,
        currentlocation=file_obj_path,
        removedtime=None,
        size=113318,
        checksum="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
        checksumtype="sha256",
    )


@pytest.fixture()
def event(db, file_obj):
    event = Event.objects.create(
        event_id=uuid.uuid4(),
        file_uuid=file_obj,
        event_type="message digest calculation",
        event_detail='program="python"; module="hashlib.sha256()"',
        event_outcome_detail="d10bbb2cddc343cd50a304c21e67cb9d5937a93bcff5e717de2df65e0a6309d6",
    )
    event_agent = Agent.objects.create(
        identifiertype="preservation system", identifiervalue="Archivematica-1.9"
    )
    event.agents.add(cls.event_agent)

    return event


@pytest.mark.django_db
def test_transfer_mets_structmap_format(
    tmp_path, transfer, file_obj, subdir_path, empty_subdir_path, file_path
):
    mets_path = tmp_path / "METS.xml"
    write_mets(
        str(mets_path), str(tmp_path), "transferDirectory", "transfer_id", transfer.uuid
    )
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()
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
        ".//mets:structMap/mets:div/mets:div/mets:div/@LABEL", namespaces=mets_xml.nsmap
    )
    file_ids = mets_xml.xpath(
        ".//mets:structMap/mets:div/mets:div/mets:div/mets:fptr/@FILEID",
        namespaces=mets_xml.nsmap,
    )

    assert len(mets_doc.all_files()) == 4

    # Test that we have physical and logical structmaps
    assert len(structmap_types) == 2
    assert "physical" in structmap_types
    assert "logical" in structmap_types

    # Test that our physical structmap is labeled properly.
    assert root_div_labels[0] == tmp_path.name
    assert subdir_div_labels[0] == subdir_path.name
    assert file_div_labels[0] == file_path.name
    assert file_ids[0] == "file-{}".format(file_obj.uuid)

    # Test that both (empty and not empty) dirs show up in logical structmap
    assert subdir_div_labels[1] == subdir_path.name
    assert subdir_div_labels[2] == empty_subdir_path.name


@pytest.mark.django_db
def test_transfer_mets_objid(tmp_path, transfer):
    mets_path = tmp_path / "METS.xml"
    write_mets(
        str(mets_path), str(tmp_path), "transferDirectory", "transfer_id", transfer.uuid
    )
    mets_doc = metsrw.METSDocument.fromfile(str(mets_path))
    mets_xml = mets_doc.serialize()
    objids = mets_xml.xpath("/*/@OBJID", namespaces=mets_xml.nsmap)

    assert len(objids) == 1
    assert objids[0] == str(transfer.uuid)
