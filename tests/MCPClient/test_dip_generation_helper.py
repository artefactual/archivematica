#!/usr/bin/env python
from unittest import mock

import dip_generation_helper
import pytest
from main.models import ArchivesSpaceDIPObjectResourcePairing


def strip_sip_directory(location):
    return location.replace("%SIPDirectory%", "")


@pytest.mark.django_db
def test_no_archivesspace_csv(sip, tmp_path):
    """It should do nothing."""
    sip_path = tmp_path / "sip"
    (sip_path / "objects" / "metadata" / "transfers").mkdir(parents=True)

    assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
    rc = dip_generation_helper.parse_archivesspace_ids(sip_path, sip.uuid)
    assert rc == 0
    assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False


@pytest.mark.django_db
def test_empty_csv(sip, tmp_path):
    """It should do nothing if the CSV is empty."""
    sip_path = tmp_path / "sip"
    metadata_dir = sip_path / "objects" / "metadata"
    metadata_dir.mkdir(parents=True)

    archivesspaceids = metadata_dir / "archivesspaceids.csv"
    archivesspaceids.touch()

    assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
    rc = dip_generation_helper.parse_archivesspace_ids(sip_path, sip.uuid)
    assert rc == 1
    assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False


@pytest.mark.django_db
def test_no_files_in_db(tmp_path, sip_file):
    """It should do nothing if no files are found in the DB."""
    sip_path = tmp_path / "sip"
    metadata_dir = sip_path / "objects" / "metadata"
    metadata_dir.mkdir(parents=True)

    metadata_csv = metadata_dir / "metadata.csv"
    metadata_csv.touch()
    metadata_csv.write_text(
        "\n".join(
            [
                "filename,dc.title,dc.description",
                f"{strip_sip_directory(sip_file.currentlocation.decode())},Mountain Tents,Tents on a mountain",
                "objects/evelyn's third photo/evelyn's third photo.jpg,Tents,Mountains blocked by tents",
            ]
        )
    )

    sip_uuid = "dne"

    assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
    rc = dip_generation_helper.parse_archivesspace_ids(sip_path, sip_uuid)
    assert rc == 0
    assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False


@pytest.mark.django_db
@mock.patch(
    "dip_generation_helper.create_archivesspace_client",
    return_value=mock.Mock(
        **{
            "find_by_id.return_value": [
                {"id": "/repositories/2/archival_objects/752250"}
            ]
        }
    ),
)
def test_parse_to_db(create_archivesspace_client, sip, sip_file, tmp_path):
    """
    It should create an entry in ArchivesSpaceDIPObjectResourcePairing for each file in archivesspaceids.csv
    It should match the reference ID to a resource ID.
    """
    sip_path = tmp_path / "sip"
    metadata_dir = sip_path / "objects" / "metadata"
    metadata_dir.mkdir(parents=True)

    archivesspaceids = metadata_dir / "archivesspaceids.csv"
    archivesspaceids.touch()
    archivesspaceids.write_text(
        f"{strip_sip_directory(sip_file.currentlocation.decode())},a118514fab1b2ee6a7e9ad259e1de355"
    )

    assert ArchivesSpaceDIPObjectResourcePairing.objects.all().exists() is False
    rc = dip_generation_helper.parse_archivesspace_ids(sip_path, sip.uuid)
    assert rc == 0
    assert len(ArchivesSpaceDIPObjectResourcePairing.objects.all()) == 1
    r = ArchivesSpaceDIPObjectResourcePairing.objects.all()[0]
    assert str(r.dipuuid) == str(sip.uuid)
    assert str(r.fileuuid) == str(sip_file.uuid)
    assert r.resourceid == "/repositories/2/archival_objects/752250"
