import pathlib
import uuid
from unittest import mock

import pytest
import pytest_django

from archivematica.dashboard.components import helpers
from archivematica.dashboard.main import models
from archivematica.dashboard.main.models import SIP
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import Transfer
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import post_store_aip_hook


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


@pytest.fixture()
def archivesspace_setting():
    models.DashboardSetting.objects.set_dict(
        "upload-archivesspace_v0.0",
        {
            "base_url": "http://foobar.tld",
            "user": "user",
            "passwd": "12345",
            "repository": "5",
            "use_statement": "",
            "xlink_show": "",
            "xlink_actuate": "",
        },
    )


@pytest.mark.django_db
def test_no_archivesspace(sip, archivesspace_components, mcp_job):
    """It should abort if no ArchivesSpaceDigitalObject found."""
    models.ArchivesSpaceDigitalObject.objects.all().delete()
    rc = post_store_aip_hook.dspace_handle_to_archivesspace(mcp_job, sip.uuid)
    assert rc == 1


@pytest.mark.django_db
@mock.patch(
    "archivematica.archivematicaCommon.storageService.get_file_info",
    return_value=[{"misc_attributes": {}}],
)
def test_no_dspace(get_file_info, sip, mcp_job):
    """It should abort if no DSpace handle found."""
    rc = post_store_aip_hook.dspace_handle_to_archivesspace(mcp_job, sip.uuid)
    assert rc == 1


@pytest.mark.django_db
@mock.patch(
    "archivematica.archivematicaCommon.storageService.get_file_info",
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
    requests_get,
    requests_post,
    get_file_info,
    sip,
    archivesspace_components,
    mcp_job,
    archivesspace_setting,
):
    """It should send the DSpace handle to ArchivesSpace."""
    rc = post_store_aip_hook.dspace_handle_to_archivesspace(mcp_job, sip.uuid)
    assert rc == 0


@pytest.fixture
def transfer(transfer, shared_directory_path):
    transfer_location = shared_directory_path / "currentlyProcessing" / "transfer"
    transfer_location.mkdir()

    transfer.currentlocation = (
        f"%sharedPath%{transfer_location.relative_to(shared_directory_path)}"
    )
    transfer.save()

    return transfer


def test_post_store_hook_deletes_transfer_directory(
    db, sip, transfer, sip_file, settings
):
    job = mock.Mock(spec=Job)

    # The transfer directory exists before calling the delete function
    transfer_path = pathlib.Path(
        transfer.currentlocation.replace("%sharedPath%", settings.SHARED_DIRECTORY, 1)
    )
    assert transfer_path.exists()

    result = post_store_aip_hook.delete_transfer_directory(job, sip.uuid)

    # The transfer directory is returned and has been deleted
    assert result == str(transfer_path)
    assert not transfer_path.exists()


@pytest.fixture
def storage_service_url() -> str:
    value = "https://ss.example.com"
    helpers.set_setting("storage_service_url", value)

    return value


@pytest.mark.django_db
@mock.patch("requests.Session.request")
def test_call_updates_storage_service_content(
    request: mock.Mock,
    dashboard_uuid: uuid.UUID,
    storage_service_url: str,
    transfer: models.Transfer,
    sip: models.SIP,
    sip_file: models.File,
    mcp_job: Job,
    settings: pytest_django.fixtures.SettingsWrapper,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Disable ES indexing.
    settings.SEARCH_ENABLED = "aips"

    arrangement = models.SIPArrange.objects.create(
        file_uuid=sip_file.uuid, transfer_uuid=transfer.uuid
    )
    mcp_job.args = ["post_store_aip_hook", str(sip.uuid)]

    post_store_aip_hook.call([mcp_job])

    assert mcp_job.get_exit_code() == 0

    arrangement.refresh_from_db()
    assert arrangement.aip_created

    assert [r.message for r in caplog.records] == [
        "Skipping indexing: Transfers indexing is currently disabled."
    ]

    assert mcp_job.get_stdout().splitlines() == [
        f"Checking if transfer {transfer.uuid} is fully stored...",
        f"Transfer {transfer.uuid} fully stored, sending delete request to storage service, deleting from transfer backlog",
        f"SIP {sip.uuid} not associated with an ArchivesSpace component",
    ]
    assert mcp_job.get_stderr().splitlines() == []

    # Verify Storage Service calls.
    request.assert_has_calls(
        [
            # Delete backlog transfer.
            mock.call(
                "POST",
                f"{storage_service_url}/api/v2/file/{transfer.uuid}/delete_aip/",
                data=None,
                json={
                    "event_reason": "All files in Transfer are now in AIPs.",
                    "pipeline": str(dashboard_uuid),
                    "user_email": "archivematica system",
                    "user_id": 0,
                },
            ),
            # Trigger Storage Service callback.
            mock.call(
                "GET",
                f"{storage_service_url}/api/v2/file/{sip.uuid}/send_callback/post_store/",
                allow_redirects=True,
            ),
        ],
        any_order=True,
    )


@pytest.fixture
def test_transfer() -> Transfer:
    transfer_id = str(uuid.uuid4())
    return Transfer.objects.create(uuid=transfer_id, currentlocation="")


@pytest.fixture
def test_sip() -> SIP:
    sip_id = str(uuid.uuid4())
    return SIP.objects.create(uuid=sip_id, currentpath="")


@pytest.fixture
def test_file(test_transfer: Transfer, test_sip: SIP) -> File:
    return File.objects.create(
        transfer_id=test_transfer.uuid,
        sip_id=test_sip.uuid,
        currentlocation=b"test/location",
        originallocation=b"test/original",
    )


@pytest.mark.django_db
def test_find_transfer_ids_by_unit_uuid_returns_transfer_ids_when_given_sip_uuid(
    test_file: File,
) -> None:
    result = post_store_aip_hook.find_transfer_ids_by_unit_uuid(str(test_file.sip_id))
    result_strs = {str(r) for r in result}
    assert result_strs == {str(test_file.transfer_id)}


@pytest.mark.django_db
def test_find_transfer_ids_by_unit_uuid_returns_transfer_ids_when_given_transfer_uuid(
    test_file: File,
) -> None:
    result = post_store_aip_hook.find_transfer_ids_by_unit_uuid(
        str(test_file.transfer_id)
    )
    result_strs = {str(r) for r in result}
    assert result_strs == {str(test_file.transfer_id)}
