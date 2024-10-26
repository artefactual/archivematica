import os
import uuid
from unittest import mock

import create_aic_mets
import namespaces as ns
import pytest
from lxml import etree

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def extract_file_mock(aip_uuid, mets_in_aip, mets_path):
    with open(mets_path, "w") as f:
        f.write("<placeholder></placeholder>")


@pytest.mark.django_db
@mock.patch("fileOperations.addFileToSIP")
@mock.patch("databaseFunctions.insertIntoDerivations")
@mock.patch("storageService.extract_file", side_effect=extract_file_mock)
@mock.patch(
    "create_mets_v2.getDublinCore",
    return_value=etree.Element(
        ns.dctermsBNS + "dublincore", nsmap={"dcterms": ns.dctermsNS, "dc": ns.dcNS}
    ),
)
@mock.patch("create_mets_v2.SIPMetadataAppliesToType")
def test_create_aic_mets(
    SIPMetadataAppliesToType,
    getDublinCore,
    extract_file,
    insertIntoDerivations,
    addFileToSIP,
    tmp_path,
):
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

    job = mock.Mock()
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
        f"{aip1_name}-{aip1_uuid}",
        f"{aip2_name}-{aip2_uuid}",
    ]
