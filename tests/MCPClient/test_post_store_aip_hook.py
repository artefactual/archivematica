import pathlib
from unittest import mock

import post_store_aip_hook
import pytest
from client.job import Job
from main import models


@pytest.fixture()
def archivesspace_components(sip):
    models.ArchivesSpaceDigitalObject.objects.create(
        remoteid="/repositories/2/digital_objects/211",
        sip=sip,
        title="Digital Object",
        started=True,
        resourceid="/repositories/2/archival_objects/8887",
        label="",
    )


def test_no_archivesspace(sip, archivesspace_components):
    """It should abort if no ArchivesSpaceDigitalObject found."""
    models.ArchivesSpaceDigitalObject.objects.all().delete()
    rc = post_store_aip_hook.dspace_handle_to_archivesspace(
        Job("stub", "stub", []), sip.uuid
    )
    assert rc == 1


@mock.patch(
    "storageService.get_file_info",
    return_value=[{"misc_attributes": {}}],
)
def test_no_dspace(get_file_info, sip):
    """It should abort if no DSpace handle found."""
    rc = post_store_aip_hook.dspace_handle_to_archivesspace(
        Job("stub", "stub", []), sip.uuid
    )
    assert rc == 1


@mock.patch(
    "storageService.get_file_info",
    return_value=[{"misc_attributes": {"handle": "123456789/41"}}],
)
@mock.patch(
    "requests.post",
    side_effect=[
        mock.Mock(**{"json.return_value": {"session": "session-id"}}),
        mock.Mock(status_code=200),
    ],
)
@mock.patch(
    "requests.get",
    return_value=mock.Mock(
        **{
            "json.return_value": {
                "file_versions": [
                    {
                        "file_uri": "123456789/41",
                        "use_statement": "text-data",
                        "xlink_actuate_attribute": "none",
                        "xlink_show_attribute": "embed",
                    },
                ],
            }
        }
    ),
)
def test_dspace_handle_to_archivesspace(
    requests_get, requests_post, get_file_info, sip, archivesspace_components
):
    """It should send the DSpace handle to ArchivesSpace."""
    rc = post_store_aip_hook.dspace_handle_to_archivesspace(
        Job("stub", "stub", []), sip.uuid
    )
    assert rc == 0


@pytest.fixture
def shared_dir(tmp_path):
    result = tmp_path / "sharedDirectory"
    result.mkdir()
    return result


@pytest.fixture
def processing_dir(shared_dir):
    result = shared_dir / "currentlyProcessing"
    result.mkdir()
    return result


@pytest.fixture
def sip(db):
    return models.SIP.objects.create()


@pytest.fixture
def transfer(transfer, shared_dir, processing_dir):
    transfer_location = processing_dir / "transfer"
    transfer_location.mkdir()

    transfer.currentlocation = (
        f"%sharedPath%{transfer_location.relative_to(shared_dir)}"
    )
    transfer.save()

    return transfer


@pytest.fixture
def file_(db, sip, transfer):
    return models.File.objects.create(sip=sip, transfer=transfer)


@pytest.fixture
def custom_settings(settings, shared_dir, processing_dir):
    settings.SHARED_DIRECTORY = f"{shared_dir}/"
    settings.PROCESSING_DIRECTORY = f"{processing_dir}/"
    return settings


def test_post_store_hook_deletes_transfer_directory(
    db, sip, transfer, file_, custom_settings
):
    job = mock.Mock(spec=Job)

    # The transfer directory exists before calling the delete function
    transfer_path = pathlib.Path(
        transfer.currentlocation.replace(
            "%sharedPath%", custom_settings.SHARED_DIRECTORY, 1
        )
    )
    assert transfer_path.exists()

    result = post_store_aip_hook.delete_transfer_directory(job, sip.uuid)

    # The transfer directory is returned and has been deleted
    assert result == str(transfer_path)
    assert not transfer_path.exists()
