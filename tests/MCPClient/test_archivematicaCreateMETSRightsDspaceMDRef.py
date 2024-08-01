import pathlib
from unittest import mock

import namespaces as ns
import pytest
from archivematicaCreateMETSRightsDspaceMDRef import (
    archivematicaCreateMETSRightsDspaceMDRef,
)
from client.job import Job
from create_mets_v2 import MetsState
from main import models


@pytest.fixture
def transfer_data(transfer, transfer_directory_path):
    fixtures_dir = pathlib.Path(__file__).parent / "fixtures" / "dspace"

    objects_dir = transfer_directory_path / "objects"
    objects_dir.mkdir()

    # Add a DSpace item with a PDF and a METS file.

    item1_dir = objects_dir / "ITEM_2429-2700"
    item1_dir.mkdir()

    item1_path = item1_dir / "bitstream.pdf"
    item1_path.touch()

    item1_file = models.File.objects.create(
        transfer=transfer,
        currentlocation=f"%SIPDirectory%{item1_path.relative_to(transfer_directory_path)}".encode(),
    )

    item1_mets_path = item1_dir / "mets.xml"
    with (fixtures_dir / "mets_item1.xml").open() as mets:
        item1_mets_path.write_text(mets.read())

    item1_mets_file = models.File.objects.create(
        transfer=transfer,
        currentlocation=f"%SIPDirectory%{item1_mets_path.relative_to(transfer_directory_path)}".encode(),
    )

    # Add a second DSpace item with a PDF and a METS file.

    item2_dir = objects_dir / "SOMEOTHERITEM"
    item2_dir.mkdir()

    item2_path = item2_dir / "bitstream.pdf"
    item2_path.touch()

    item2_file = models.File.objects.create(
        transfer=transfer,
        currentlocation=f"%SIPDirectory%{item2_path.relative_to(transfer_directory_path)}".encode(),
    )

    item2_mets_path = item2_dir / "mets.xml"
    with (fixtures_dir / "mets_item2.xml").open() as mets:
        item2_mets_path.write_text(mets.read())

    item2_mets_file = models.File.objects.create(
        transfer=transfer,
        currentlocation=f"%SIPDirectory%{item2_mets_path.relative_to(transfer_directory_path)}".encode(),
    )

    return {
        "item1_path": item1_path,
        "item1_file": item1_file,
        "item1_mets_file": item1_mets_file,
        "item1_mets_path": item1_mets_path,
        "item2_path": item2_path,
        "item2_file": item2_file,
        "item2_mets_file": item2_mets_file,
        "item2_mets_path": item2_mets_path,
        "transfer_dir": transfer_directory_path,
        "transfer": transfer,
    }


@pytest.mark.django_db
def test_archivematicaCreateMETSRightsDspaceMDRef(transfer_data):
    job = mock.Mock(spec=Job)
    state = MetsState()
    file_path = transfer_data["item1_path"].relative_to(transfer_data["transfer_dir"])

    result = archivematicaCreateMETSRightsDspaceMDRef(
        job,
        transfer_data["item1_file"].uuid,
        file_path,
        transfer_data["transfer"].uuid,
        transfer_data["item1_path"],
        state,
    )
    assert state.error_accumulator.error_count == 0

    # One dmdSec is created for each METS file.
    assert len(result) == 2

    # Verify the attributes of the returned mdRef elements.
    dmd_secs = sorted([d.attrib for d in result], key=lambda d: d[f"{ns.xlinkBNS}href"])

    assert dmd_secs == [
        {
            "LABEL": f"mets.xml-{transfer_data['item1_mets_file'].uuid}",
            "MDTYPE": "OTHER",
            "OTHERMDTYPE": "METSRIGHTS",
            "LOCTYPE": "OTHER",
            "OTHERLOCTYPE": "SYSTEM",
            "XPTR": "xpointer(id('rightsMD_371 rightsMD_374 rightsMD_384 rightsMD_393 rightsMD_401 rightsMD_409 rightsMD_417 rightsMD_425'))",
            f"{ns.xlinkBNS}href": str(
                transfer_data["item1_mets_path"].relative_to(
                    transfer_data["transfer_dir"]
                )
            ),
        },
        {
            "LABEL": f"mets.xml-{transfer_data['item2_mets_file'].uuid}",
            "MDTYPE": "OTHER",
            "OTHERMDTYPE": "METSRIGHTS",
            "LOCTYPE": "OTHER",
            "OTHERLOCTYPE": "SYSTEM",
            "XPTR": "xpointer(id('rightsMD_435 rightsMD_438 rightsMD_448 rightsMD_457 rightsMD_465 rightsMD_473 rightsMD_481 rightsMD_489'))",
            f"{ns.xlinkBNS}href": str(
                transfer_data["item2_mets_path"].relative_to(
                    transfer_data["transfer_dir"]
                )
            ),
        },
    ]

    job.pyprint.assert_has_calls(
        [
            mock.call(transfer_data["item1_file"].uuid, file_path),
            mock.call(str(transfer_data["item1_path"].parent)),
            mock.call(str(transfer_data["item2_path"].parent)),
            mock.call(str(transfer_data["item2_mets_path"])),
            mock.call("continue"),
        ],
        # os.listdir returns files in arbitrary order.
        any_order=True,
    )


@pytest.mark.django_db
@mock.patch(
    "archivematicaCreateMETSRightsDspaceMDRef.createMDRefDMDSec",
    side_effect=Exception("error"),
)
def test_archivematicaCreateMETSRightsDspaceMDRef_handle_exceptions(
    createMDRefDMDSec, transfer_data
):
    job = mock.Mock(spec=Job)
    state = MetsState()
    file_path = transfer_data["item1_path"].relative_to(transfer_data["transfer_dir"])

    result = archivematicaCreateMETSRightsDspaceMDRef(
        job,
        transfer_data["item1_file"].uuid,
        file_path,
        transfer_data["transfer"].uuid,
        transfer_data["item1_path"],
        state,
    )
    assert state.error_accumulator.error_count == 1

    assert len(result) == 0

    assert job.pyprint.mock_calls == [
        mock.call(transfer_data["item1_file"].uuid, file_path),
        mock.call(
            "Error creating mets dspace mdref",
            transfer_data["item1_file"].uuid,
            file_path,
            file=mock.ANY,
        ),
        mock.call(mock.ANY, ("error",), file=mock.ANY),
    ]

    createMDRefDMDSec.assert_called_once_with(
        f"mets.xml-{transfer_data['item1_mets_file'].uuid}",
        str(transfer_data["item1_mets_path"]),
        str(
            transfer_data["item1_mets_path"].relative_to(transfer_data["transfer_dir"])
        ),
    )
