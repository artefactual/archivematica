# -*- coding: utf8
from __future__ import unicode_literals
import os
import uuid

from lxml import etree

import namespaces as ns

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

import create_aic_mets


def extract_file_mock(aip_uuid, mets_in_aip, mets_path):
    with open(mets_path, "w") as f:
        f.write("<placeholder></placeholder>")


def test_create_aic_mets(db, mocker, tmp_path):
    mocker.patch("fileOperations.addFileToSIP")
    mocker.patch("databaseFunctions.insertIntoDerivations")
    mocker.patch("storageService.extract_file", side_effect=extract_file_mock)
    mocker.patch(
        "create_mets_v2.getDublinCore",
        return_value=etree.Element(
            ns.dctermsBNS + "dublincore", nsmap={"dcterms": ns.dctermsNS, "dc": ns.dcNS}
        ),
    )
    mocker.patch("create_mets_v2.SIPMetadataAppliesToType")

    # The client script expects an AIC directory that contains files whose
    # filenames are AIP UUIDs and their contents are the AIP names, so we create
    # a couple of those files here
    aic_uuid = str(uuid.uuid4())
    aic_dir = tmp_path / "aic"
    aic_dir.mkdir()
    objects_dir = aic_dir / "objects"
    objects_dir.mkdir()

    # AIP 1
    aip1_uuid = str(uuid.uuid4())
    aip1_name = "AIP 1"
    aip1 = objects_dir / aip1_uuid
    aip1.write_text(aip1_name)

    # AIP 2
    aip2_uuid = str(uuid.uuid4())
    aip2 = objects_dir / aip2_uuid
    aip2_name = "AIP 2"
    aip2.write_text(aip2_name)

    # The AIC METS is created in the metadata directory of the AIC
    (aic_dir / "metadata").mkdir()

    job = mocker.Mock()
    create_aic_mets.create_aic_mets(aic_uuid, str(aic_dir), job)

    # The AIC METS has a new UUID suffixed name, so we search for it instead of
    # opening it directly, and then parse it
    aic_metadata_files = list((aic_dir / "metadata").glob("*.xml"))
    aic_mets = etree.parse(str(aic_metadata_files[0]))

    # The fileSec of the AIC METS contains file pointers to each AIP
    listed_aips = [
        e.get("ID")
        for e in aic_mets.findall("mets:fileSec//mets:file", namespaces=ns.NSMAP)
    ]
    assert sorted(listed_aips) == [
        "{}-{}".format(aip1_name, aip1_uuid),
        "{}-{}".format(aip2_name, aip2_uuid),
    ]
